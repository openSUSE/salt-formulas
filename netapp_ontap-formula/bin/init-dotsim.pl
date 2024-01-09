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
# - read multipath devices from domain XML file

use v5.26.1;
use Archive::Tar;
use Expect;
use File::Temp;
use File::pushd;
use Getopt::Long qw(:config auto_version);
use Sys::Virt;

our $VERSION = '0.1';
my $source;
my $mpaths;
my $domain;
my $cluster;
my $force;
my $only_vm;
my $address;
my $netmask;
my $gateway;
my $passphrase;
my $reset;

sub usage {
    print <<~'EOH'
    Please specify all of the following arguments for this script to proceed:
    --address, --netmask, --gateway : IP details for the VM to use on the node management interface
    --cluster                       : Name to give the cluster
    --domain                        : Path to an existing Libvirt domain XML file the VM should be started from
    --mpaths                        : Comma separated list of four multipath devices the individual disk images should be written to
    --passphrase                    : Passphrase to set for the default "admin" user
    --source                        : Path to the NetApp provided OVA image (aka tarball)
    EOH
    ; exit;
}

GetOptions(
    "address=s"    => \$address,
    "cluster=s"    => \$cluster,
    "domain=s"     => \$domain,
    "force"        => \$force,
    "gateway=s"    => \$gateway,
    "mpaths=s"     => \$mpaths,
    "netmask=s"    => \$netmask,
    "only_vm"      => \$only_vm,
    "passphrase=s" => \$passphrase,
    "reset"        => \$reset,
    "source=s"     => \$source,
    "help" =>      sub { usage(); }
) or exit;
usage() unless ( $address && $netmask && $gateway && $cluster && $domain && $mpaths && $passphrase && $source );

my $attempts = 1;
my $vircon   = Sys::Virt->new( uri => 'qemu:///system' );
my @paths;
my @vmdks;

sub extract {
    print("Extracting ...\n");
    if ( !-e $source ) {
        die "No OVA file at $source, aborting";
    }
    my $tar = Archive::Tar->new();
    $tar->read($source);
    $tar->extract();
}

sub convert {
    print("Converting ...\n");
    while ( my $vmdk = glob("*.vmdk") ) {
        system("qemu-img convert -p -fvmdk -Oraw $vmdk $vmdk.raw");
        push @vmdks, "$vmdk.raw";
    }
}

sub check {
    print("Validating target disks ...\n");
    foreach my $target ( split( ',', $mpaths ) ) {
        my $path = "/dev/disk/by-id/dm-uuid-mpath-$target";
        if ( !-b $path ) {
            print("Disk at $path is not valid.\n");
            next;
        }
        my $status = system("partx -rgoNR $path >/dev/null 2>&1");
        if ( $status != 0 || $force ) {
            push @paths, $path;
        }
        else {
            print("Disk at $path seems to contain an existing file system. Refusing destruction without --force.\n");
        }
    }
}

sub dd {
    print("Writing ...\n");
    my $loop = 0;
    foreach my $vmdk (@vmdks) {
        system("dd if=$vmdk of=@paths[$loop] bs=16M status=progress");
        $loop++;
    }
}

sub vm {
    my $reinit = 0;
    my $xml;
    my $fh;

    open( $fh, '<', $domain ) or die "Cannot open XML file $domain";
    { local $/; $xml = <$fh> };
    my $domain = $vircon->create_domain($xml);
    my $domid  = $domain->get_id();
    print("\nStarted domain with ID $domid");
    my $domvp = `virsh vncdisplay $domid`;
    print(", VNC host is $domvp");
    my $console = Expect->spawn("virsh console $domid")
      or die "Unable to spawn console";
    $console->restart_timeout_upon_receive(1);

    sub handle_boot {
        my $prompt   = 'VLOADER>';
        my @commands = (
            "set console=comconsole\n",
            "set comconsole_speed=115200\n",
            "boot\n",
        );
        sub boot {
            $console->expect(20,
                [
                    qr/Hit \[Enter\] to boot immediately, or any other key for command prompt\./
                ]
            );
            $console->send( $_[0] );
        }
        boot('x');
        foreach my $command (@commands) {
            $console->expect( 10, $prompt );
            $console->send($command);
        }
        if ($reset) {
            my %dialogue = (
                '* Press Ctrl-C for Boot Menu. *'                          => "\cC",
                'Selection (1-11)?'                                        => "4\n",
                'Zero disks, reset config and install a new file system?'  => "yes\n",
                'This will erase all the data on the disks, are you sure?' => "yes\n",
                'Rebooting to finish wipeconfig request.'                  => '',
            );
            my $prompts = join( '|', map { qr{\Q$_\E} } keys %dialogue );
            $console->expect(60,
                -re => $prompts,
                sub {
                    my $ex      = shift;
                    my $matched = $ex->match;
                    my $answer  = delete $dialogue{$matched};
                    $ex->send($answer);
                    exp_continue if keys %dialogue;
                }
            );
            boot("\n");
        }
        $console->expect(480,
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
                timeout => sub {
                    print("System did not finish booting in time.\n");
                    # what to do now ?
                }
            ]
        );
    }

    sub handle_setup {
        $console->expect(10,
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
        );
        my $prompt   = '::>';
        my @commands = (
            "network interface del -vserver Cluster -lif clus1\n",
            "network port modify -node localhost -port e0a -ipspace Default\n",
            "network interface create -vserver Default -lif mgmt -role node-mgmt -address $address -netmask $netmask -home-node localhost -home-port e0a\n",
            "network route create -vserver Default -destination 0.0.0.0/0 -gateway $gateway\n",
            "cluster setup\n",
        );
        foreach my $command (@commands) {
            $console->expect( 10, $prompt );
            $console->send($command);
        }
        my %dialogue = (
            "Press <space> to page down, <return> for next line, or 'q' to quit..."            => 'q',
            'Type yes to confirm and continue {yes}:'                                          => 'yes',
            'Enter the node management interface port'                                         => 'e0a',
            'Enter the node management interface IP address [10.168.0.96]:'                    => '',
            'Enter the node management interface netmask [255.255.254.0]:'                     => '',
            'Enter the node management interface default gateway [10.168.1.254]:'              => '',
            'Otherwise, press Enter to complete cluster setup using the command line'          => '',
            'Do you want to create a new cluster or join an existing cluster? {create, join}:' => 'create',
            'Do you intend for this node to be used as a single node cluster? {yes, no} [no]:' => 'yes',
            "Enter the cluster administrator's (username \"admin\") password:"                 => "$passphrase",
            'Retype the password:'                                                             => "$passphrase",
            'Enter the cluster name:'                                                          => "$cluster",
        );
        $console->expect( 10, 'Welcome to the cluster setup wizard.' );
        my $prompts = join( '|', map { qr {\Q$_\E} } keys %dialogue );
        $console->expect(10,
            -re => $prompts,
            sub {
                my $ex      = shift;
                my $matched = $ex->match;
                my $answer  = delete $dialogue{$matched};
                if ( $answer ne 'q' ) { $answer = $answer . "\n" }
                $ex->send($answer);
                sleep(1);
                exp_continue if keys %dialogue;
            }
        );
        $console->expect(300,
            [
                qr/Creating cluster $cluster/,
                sub {
                    exp_continue;
                }
            ],
            [
                qr/Starting cluster support services/
	    ]
        );
        $console->expect(10,
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
                qr/${cluster}::>/,
                sub {
                    my $ex = shift;
                    $ex->send("version\n");
                }
            ],
        );
    }

    sub handle_reinit {
        if ($reinit) {
            $console->soft_close();
            $domain->destroy();
            if ( $attempts == 2 ) {
                die("System is still broken after two attempts, giving up.\n");
            }
            if ($only_vm) {
                die("Unsetting --only_vm in an attempt to start from scratch!\n"
                );
                $only_vm = 0;
            }
            $force = 1;
            $attempts++;
            run();
        }
    }

    handle_boot();
    handle_reinit();
    handle_setup();
    $console->soft_close();
    handle_reinit(); #why here?
}

sub run {
    if ( !$only_vm ) {
        check();
        my $good_paths = @paths;
        if ( $good_paths < 4 ) {
            die("Not enough writeable disks, aborting.\n");
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
