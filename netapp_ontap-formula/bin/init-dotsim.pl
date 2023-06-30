#!/usr/bin/perl
# Experimental script to initialize a NetApp Data ONTAP simulator on a KVM hypervisor
# Copyright (C) 2023 Georg Pfuetzenreuter <georg.pfuetzenreuter@suse.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# to-do:
# - clean up, move expect prompts/answers to a hash or similar
# - handle CLI prompts better, sometimes the answers don't align with the prompts
# - read multipath devices from domain XML file

use v5.26.1;
use Archive::Tar;
use Expect;
use File::pushd;
use File::Temp;
use Getopt::Long;
use Sys::Virt;

my $source;
my $mpaths;
my $domain;
my $force;
my $only_vm;
my $address;
my $netmask;
my $gateway;
my $passphrase;
my $reset;

GetOptions
	("source=s" => \$source, "mpaths=s" => \$mpaths, "domain=s", => \$domain, "force" => \$force, "only_vm" => \$only_vm,
	 "address=s" => \$address, "netmask=s" => \$netmask, "gateway=s" => \$gateway, "passphrase=s" => \$passphrase, "reset" => \$reset
	)
	or die "\nFailed to set arguments";

if(!$source){die "Please specify the full path to an OVA image to use using --source"}
if(!$mpaths){die "Please specify the multipath devices to write to using --mpaths. Pass them comma separated in the order to use."}
if(!$domain){die "Please specify the Libvirt domain XML file to use using --name"}
if(!$address||!$netmask||!$gateway){die "Please specify --address, --netmask and --gateway"}
if(!$passphrase){die "Please specify an admin passphrase using --passphrase"}

my @paths;
my @vmdks;
my $vircon = Sys::Virt->new(uri => 'qemu:///system');
my $attempts = 1;

sub extract {
  print("Extracting ...\n");
  if (! -e $source) {
    die "No OVA file at $source, aborting";
  }
  my $tar=Archive::Tar->new();
  $tar->read($source);
  $tar->extract();
}

sub convert {
  print("Converting ...\n");
  while (my $vmdk = glob("*.vmdk")) {
    system("qemu-img convert -p -fvmdk -Oraw $vmdk $vmdk.raw");
    push @vmdks, "$vmdk.raw";
  }
}

sub check {
  print("Validating target disks ...\n");
  foreach my $target (split(',', $mpaths)) {
    my $path = "/dev/disk/by-id/dm-uuid-mpath-$target";
    if (! -b $path) {
      print("Disk at $path is not valid.\n");
      next;
    }
    my $status = system("partx -rgoNR $path >/dev/null 2>&1");
    if ($status != 0 || $force) {
      push @paths, $path;
    } else {
      print("Disk at $path seems to contain an existing file system. Refusing destruction without --force.\n");
    }
  }
}

sub dd {
  print("Writing ...\n");
  my $loop = 0;
  foreach my $vmdk (@vmdks) {
    system("dd if=$vmdk of=@paths[$loop] bs=16M status=progress");
    $loop ++;
  }
}  

sub vm {
  my $reinit = 0;
  my $xml;
  my $fh;
  open($fh, '<', $domain) or die "Cannot open XML file $domain";
  { local $/; $xml = <$fh> };
  my $domain = $vircon->create_domain($xml);
  my $domid = $domain->get_id();
  print("\nStarted domain with ID $domid");
  my $domvp = `virsh vncdisplay $domid`;
  print(", VNC host is $domvp");
  my $firstboot = Expect->spawn("virsh console $domid") or die "Unable to spawn console";
  $firstboot->restart_timeout_upon_receive(1);
  $firstboot->expect(10,
    [
      qr/Hit \[Enter\] to boot immediately, or any other key for command prompt\./,
      sub {
        my $ex = shift;
	$ex->send("j");
      }
    ]
  );
  $firstboot->expect(10,
    [
     qr/VLOADER>/,
     sub {
       my $ex = shift;
       $ex->send("set console=comconsole\n");
     }
    ]
  );
  $firstboot->expect(10,
    [
     qr/VLOADER>/,
     sub {
       my $ex = shift;
       $ex->send("set comconsole_speed=115200\n");
     }
    ]
  );
  $firstboot->expect(10,
    [
     qr/VLOADER>/,
     sub {
       my $ex = shift;
       $ex->send("boot\n");
     }
    ],
  );
  if ($reset) {
    $firstboot->expect(60,
      [
       qr/\* Press Ctrl-C for Boot Menu\. \*/,
       sub {
         my $ex = shift;
         $ex->send("\cC");
         exp_continue;
       }
      ],
      [
       qr/Selection \(1-11\)\?/,
       sub {
         my $ex = shift;
         $ex->send("4\n");
         exp_continue;
       }
      ],
      [
       qr/Zero disks, reset config and install a new file system\?:/,
       sub {
         my $ex = shift;
         $ex->send("yes\n");
         exp_continue;
       }
      ],
      [
       qr/This will erase all the data on the disks, are you sure\?:/,
       sub {
         my $ex = shift;
         $ex->send("yes\n");
         exp_continue;
       }
      ],
      [
       qr/Rebooting to finish wipeconfig request\./
      ]
    );
    $firstboot->expect(30,
      [
        qr/Hit \[Enter\] to boot immediately, or any other key for command prompt\./,
        sub {
          my $ex = shift;
          $ex->send("\n");
        }
      ]
    );
  }
  $firstboot->expect(480,
    [
      qr/(?:System initialization has completed successfully\.|Welcome to the cluster setup wizard\.)/,
    ],
    [
      qr/DUMPCORE: START/,
      sub {
        print("System is broken, starting from scratch...\n");
        $reinit = 1;
      }
    ],
    [
      timeout =>
      sub {
        print("System did not finish booting in time.\n");
	# what to do now ?
      }
    ]
  );
  if ($reinit)
  {
    $firstboot->soft_close();
    $domain->destroy();
    if ($attempts == 2) {
      die("System is still broken after two attempts, giving up.\n");
    }
    if ($only_vm) {
      die("Unsetting --only_vm in an attempt to start from scratch!\n");
      $only_vm = 0;
    } 
    $force = 1;
    $attempts ++;
    run();
  }
  $firstboot->expect(10,
    [
      qr/Type yes to confirm and continue \{yes\}:/,
      sub {
        my $ex = shift;
	$ex->send("exit\n");
	exp_continue;
      }
    ],
    [
      qr/login:/,
      sub {
        my $ex = shift;
	$ex->send("admin\n");
	exp_continue;
      }
    ],
    [
      qr/::>/,
      sub {
        my $ex = shift;
	$ex->send("network interface del -vserver Cluster -lif clus1\n");
      }
    ]
  );
  $firstboot->expect(10,
    [
      qr/::>/,
      sub {
        my $ex = shift;
	$ex->send("network port modify -node localhost -port e0a -ipspace Default\n");
      }
    ]
  );
  $firstboot->expect(10,
    [
      qr/::>/,
      sub {
        my $ex = shift;
	$ex->send("network interface create -vserver Default -lif mgmt -role node-mgmt -address $address -netmask $netmask -home-node localhost -home-port e0a\n");
      }
    ]
  );
  $firstboot->expect(10,
    [
      qr/::>/,
      sub {
        my $ex = shift;
	$ex->send("network route create -vserver Default -destination 0.0.0.0/0 -gateway $gateway\n");
      }
    ]
  );
  $firstboot->expect(10,
    [
      qr/::>/,
      sub {
        my $ex = shift;
	$ex->send("cluster setup\n");
	exp_continue;
      }
    ],
    [
      qr/Press <space> to page down, <return> for next line, or 'q' to quit\.\.\./,
      sub {
        my $ex = shift;
	$ex->send("q\n");
	exp_continue;
      }
    ],
    [
      qr/Type yes to confirm and continue \{yes\}:/,
      sub {
        my $ex = shift;
	$ex->send("yes\n");
	exp_continue;
      }
    ],
    [
      qr/Enter the node management interface port/,
      sub {
        my $ex = shift;
	$ex->send("e0a\n");
	exp_continue;
      }
    ],
    [
      qr/Enter the node management interface IP address \[10\.168\.0\.96\]:/,
      sub {
        my $ex = shift;
	$ex->send("\n");
	exp_continue;
      }
    ],
    [
      qr/Enter the node management interface netmask \[255\.255\.254\.0\]:/,
      sub {
        my $ex = shift;
	$ex->send("\n");
	exp_continue;
      }
    ],
    [
      qr/Enter the node management interface default gateway \[10\.168\.1\.254\]:/,
      sub {
        my $ex = shift;
	$ex->send("\n");
	exp_continue;
      }
    ],
    [
      qr/Otherwise, press Enter to complete cluster setup using the command line/,
      sub {
        my $ex = shift;
	$ex->send("\n");
	exp_continue;
      }
    ],
    [
      qr/Do you want to create a new cluster or join an existing cluster\? \{create, join\}:/,
      sub {
        my $ex = shift;
	$ex->send("create\n");
	exp_continue;
      }
    ],
    [
      qr/Do you intend for this node to be used as a single node cluster\? \{yes, no\} \[no\]:/,
      sub {
        my $ex = shift;
	$ex->send("yes\n");
	exp_continue;
      }
    ],
    [
      qr/Enter the cluster administrator's \(username "admin"\) password:/,
      sub {
        my $ex = shift;
	$ex->send("$passphrase\n");
	exp_continue;
      }
    ],
    [
      qr/Retype the password:/,
      sub {
        my $ex = shift;
	$ex->send("$passphrase\n");
	exp_continue;
      }
    ],
    [
      qr/Enter the cluster name:/,
      sub {
        my $ex = shift;
	$ex->send("labA\n");
      }
    ],
  );
  $firstboot->expect(300,
    [
      qr/Creating cluster labA/,
      sub {
	exp_continue;
      }
    ],
    [
      qr/Starting cluster support services/
    ]
  );
  $firstboot->expect(10,
    [
      qr/Enter an additional license key \[\]:/,
      sub {
        my $ex = shift;
	$ex->send("\n");
	exp_continue;
      }
    ],
    [
      qr/Enter the cluster management interface port/,
      sub {
        my $ex = shift;
	$ex->send("exit\n");
	exp_continue;
      }
    ],
    [
      qr/labA::>/,
      sub {
        my $ex = shift;
	$ex->send("version\n");
      }
    ],
  );
  $firstboot->soft_close();
  if ($reinit)
  {
    $domain->destroy();
    if ($attempts == 2) {
      die("System is still broken after two attempts, giving up.\n");
    }
    if ($only_vm) {
      die("Unsetting --only_vm in an attempt to start from scratch!\n");
      $only_vm = 0;
    } 
    $force = 1;
    $attempts ++;
    run();
  }
}

sub run {
  if (!$only_vm) {
    check();
    my $good_paths = @paths;
    if ($good_paths < 4) {
      die("Not enough writeable disks, aborting.\n")
    }
    my $outdir = tempd();
    print("Working in temporary directory $outdir\n");
    extract();
    convert();
    dd();
  }
  vm();
  print("\nDone, simulator should be reachable at $address.\n");
}

run();
