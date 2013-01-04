#!/usr/bin/perl

# This file is part of B{Domogik} project (U{http://www.domogik.org}).
#
# License
# =======
#
# B{Domogik} is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# B{Domogik} is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Domogik. If not, see U{http://www.gnu.org/licenses}.
#
# Purpose
# ==============
# SNMP agent for domogik.
#
# Implements
# ==========
# Embeded code
#
# @author: Sébastien Gallet <sgallet@gmail.com>
# @copyright: (C) 2007-2012 Domogik project
# @license: GPL(v3)
# @organization: Domogik

use strict;
#use warnings;
#use diagnostics;
use Config::Simple;
use Proc::ProcessTable;
use NetSNMP::agent (':all');
use NetSNMP::ASN qw(:all);
use CHI;
use LWP::Simple;
use JSON qw( decode_json );
use Data::Dumper;
use Log::Log4perl qw(:easy);
#use ZMQ::LibZMQ2;
#use ZMQ::Constants qw(ZMQ_REQ);

my $configuration_file = "/etc/domogik/snmp.cfg";
my $domogik_cfg = "/etc/domogik/domogik.cfg";
my $domogik_pid_dir = "/var/run/domogik/";
my $rest_ip = "127.0.0.1";
my $rest_port = "40405";
my $event_ip = "127.0.0.1";
my $event_req_port = "6559";
my $dmg_manager = "/usr/local/bin/dmg_manager";

my $domogik_oid = ".1.3.6.1.4.1.41072";

my $sub_oid_application = ".0.1";
my $sub_oid_core = ".0.2";
my $sub_oid_plugins = ".0.3";

my $oid_plugins_name = ".10.0";
my $oid_plugins_started = ".10.1";
my $oid_plugins_pid = ".10.2";
my $oid_plugins_pcpu = ".10.3";
my $oid_plugins_pmem = ".10.4";
my $oid_plugins_rss = ".10.5";
my $oid_plugins_size = ".10.6";

my $ttl_process = 10;
my $ttl_rest = 30;
my $ttl_python = 600;
my $ttl_conf = 10;
my $ttl_pid = 120;
my $ttl_zmq = 120;

my $debug = 0;

our $cache;
our $agent;
our $zmq_context;

sub compute_zmq_info {
    # Compute the zmq informations
    # Return a hash

    my $HoH_zmq = $cache->get("zmq_info");
    if ( !defined $HoH_zmq ) {
        $HoH_zmq->{ "version" } = "unknown";
#        DEBUG "dmg_snmp.pl : zmq_info NOT IN cache";
#
#        # Socket to talk to server
#        DEBUG 'Connecting to hello world server…';
#        my $requester = zmq_socket($zmq_context, ZMQ_REQ);
#        my $trendsurl = sprintf("tcp://%s:%s",$event_ip,$event_req_port );
#        zmq_connect($requester, $trendsurl);
#
#        for my $request_nbr (0..9) {
#            DEBUG "Sending request $request_nbr…";
#            zmq_send($requester, 'Hello');
#            my $reply = zmq_recv($requester);
#           $HoH_zmq->{ "version" } = "Hello world";
#            DEBUG "Received reply $request_nbr: [". zmq_msg_data($reply) .']';
#        }
        my $delay = sprintf("%ds", $ttl_zmq);
        $cache->set('zmq_info', $HoH_zmq, $delay );
    }
    return $HoH_zmq;
}

sub compute_rest_info {
    # Compute the rest informations
    # Return a hash

    my $HoH_rest = $cache->get("rest_info");
    if ( !defined $HoH_rest ) {
        DEBUG "dmg_snmp.pl : rest_info NOT IN cache";
        my $trendsurl = sprintf("http://%s:%s",$rest_ip,$rest_port );
        my $json = get( $trendsurl );
        my $decoded_json;
        eval {                          # try

            # This next line isn't Perl.  don't know what you're going for.
            #my $decoded_json = @{decode_json{shares}};

            # Decode the entire JSON
            $decoded_json = decode_json( $json );
            # you'll get this (it'll print out); comment this when done.
            #print Dumper $decoded_json;

            #DEBUG sprintf("dmg_snmp.pl : compute_rest_info json = %s", $decoded_json);
            #DEBUG sprintf("dmg_snmp.pl : compute_rest_info json = %s", $decoded_json->{'rest'});
            my @arest = $decoded_json->{'rest'};
            my $restpart;
            for $restpart ( @arest ) {
                #DEBUG sprintf("dmg_snmp.pl : compute_rest_info restpart = %s", $restpart);
                my $role;
                for $role ( @$restpart ) {
                     #DEBUG sprintf("dmg_snmp.pl : compute_rest_info arest = %s", @$restpart[$role]);
                     if ( defined $role->{'info'}->{'REST_API_version'} ) {
                        $HoH_rest->{ "rest_version" } = $role->{'info'}->{'REST_API_version'};
                        $HoH_rest->{ "version" } = $role->{'info'}->{'Domogik_version'};
                     }
                     #print "$role=$href->{$role} ";
                     #DEBUG sprintf("dmg_snmp.pl : compute_rest_info arest->{'info'}->{'REST_API_version'} = %s", @$restpart[$role]->{'info'}->{'REST_API_version'});
                }
            }
            1;
        } or do {                       # catch
            $HoH_rest->{ "rest_version" } = "unknown";
            $HoH_rest->{ "version" } = "unknown";
        };
               my $decoded_json;

        my $delay = sprintf("%ds", $ttl_rest);
        $cache->set('rest_info', $HoH_rest, $delay );
    }
    return $HoH_rest;
}

sub compute_plugin_list {
    # Compute the domogik.cfg
    # Return a sorted array of enabled plugin name

    my $PluginList = $cache->get("plugin_list");
    if ( !defined $PluginList ) {
        DEBUG "dmg_snmp.pl : plugin_list NOT IN cache";
        $PluginList = [];
        my $cfg = new Config::Simple();
        $cfg->read($domogik_cfg) or die $cfg->error();
        my $plugins = $cfg->get_block('plugins');
        my $plugin;
        foreach $plugin ( keys %$plugins ) {
             DEBUG sprintf("dmg_snmp.pl : plugin_list plugin = %s", $plugin);
             my $state = $plugins->{ $plugin };
             DEBUG sprintf("dmg_snmp.pl : plugin_list plugin value = %s", $state);
             if ('enabled' eq $state) {
                push(@$PluginList, $plugin);
             };
         };
        @$PluginList = sort(@$PluginList);
        my $delay = sprintf("%ds", $ttl_conf);
        $cache->set('plugin_list', $PluginList, $delay );
    };
    #my $core;
    #for $core ( @$CoreList ) {
    #    DEBUG sprintf("dmg_snmp.pl : compute_core_list core = %s",$core);
    #}
    return $PluginList
}

sub compute_core_list {
    # Return an array of core plugin name
    my $CoreList = $cache->get("core_list");
    if ( !defined $CoreList ) {
        DEBUG "dmg_snmp.pl : core_list NOT IN cache";
        $CoreList = [];
        my $CoreOrder = compute_core_order();
        my $core;
        foreach $core ( keys %$CoreOrder ) {
             #DEBUG sprintf("dmg_snmp.pl : compute_core_list order = %s", $core);
             #DEBUG sprintf("dmg_snmp.pl : compute_core_list core = %s", $CoreOrder->{ $core });
             push(@$CoreList, $CoreOrder->{ $core }->{ "plugin" });
             };
        my $delay = sprintf("%ds", $ttl_process);
        $cache->set('core_list', $CoreList, $delay );
    };
    #my $core;
    #for $core ( @$CoreList ) {
    #    DEBUG sprintf("dmg_snmp.pl : compute_core_list core = %s",$core);
    #}
    return $CoreList
}

sub compute_core_order {
    # Retrieve an order list of plugins core
    # Return an hash of plugin name
    #
    # (
    #     0 => 'manager',
    #     1 => 'dbmgr',
    #     ... => ...,
    # )
    my $HoH_core_order = $cache->get("core_order");
    if ( !defined $HoH_core_order ) {
        DEBUG "dmg_snmp.pl : core_order NOT IN cache";
        my $cfg = new Config::Simple();
        $cfg->read($configuration_file) or die $cfg->error();
        my $cores = $cfg->get_block('core');
        my $core;
        foreach $core ( keys %$cores ) {
             #DEBUG sprintf("dmg_snmp.pl : compute_core_order order = %s", $core);
             #DEBUG sprintf("dmg_snmp.pl : compute_core_order core = %s", $cores->{ $core });
             my $first_oid = $sub_oid_core.sprintf(".%d", $core+10);
             my $next_oid = $sub_oid_core.sprintf(".%d", $core+11);
             #DEBUG sprintf("dmg_snmp.pl : compute_core_order first_oid = %s", $first_oid);
             #DEBUG sprintf("dmg_snmp.pl : compute_core_order next_oid = %s", $next_oid);
             $HoH_core_order->{ $core } = { "plugin" => $cores->{ $core },
                                  "firstoid" => $first_oid,
                                  "nextoid" => $next_oid,
                                };
             };
        }
        my $delay = sprintf("%ds", $ttl_conf);
        $cache->set('core_order', $HoH_core_order, $delay );
    return $HoH_core_order
}

sub compute_core_pid {
    # Compute the plugin pid list from /var/run/domogik
    # Return an hash of hash of plugin pids
    #
    # (
    #     pid1 => {
    #         'plugin' => 'manager',
    #     },
    #     pid2 => {
    #         'plugin' => 'dbmgr',
    #     },
    #     ... => {
    #         ...,
    #     },
    # )
    my $HoH = $cache->get("core_pid");
    if ( !defined $HoH ) {
        DEBUG "dmg_snmp.pl : core_pid NOT IN cache";
        my @cores = @{compute_core_list()};
        my $core;
        for $core ( @cores ) {
            #DEBUG sprintf("dmg_snmp.pl : compute_core_pid core = %s", $core);
            # the filename should be passed in as a parameter
            my $filename = $domogik_pid_dir.$core.".pid";
            open FILE, $filename;
            # read the record, and chomp off the newline
            chomp(my $record = <FILE>);
            close FILE;
            #DEBUG sprintf("dmg_snmp.pl : compute_core_pid pid = %s", $record);
            $HoH->{ $record } = {
                 'plugin'  => $core,
             };
        }
        my $delay = sprintf("%ds", $ttl_pid);
        $cache->set('core_pid', $HoH, $delay );
    };
    return $HoH
}

sub compute_plugin_pid {
    # Compute the plugin pid list from /var/run/domogik
    # Return an hash of hash of plugin pids
    #
    # (
    #     pid1 => {
    #         plugin => "cron",
    #     },
    #     pid2 => {
    #         plugin => "ozwave",
    #     },
    #     ... => {
    #         ...,
    #     },
    # )
    my $HoH = $cache->get("plugin_pid");
    if ( !defined $HoH ) {
        DEBUG "dmg_snmp.pl : plugin_pid NOT IN cache";
        my @plugins = @{compute_plugin_list()};
        my $plugin;
        for $plugin ( @plugins ) {
            #DEBUG sprintf("dmg_snmp.pl : plugin_pid plugin = %s", $plugin);
            # the filename should be passed in as a parameter
            my $filename = $domogik_pid_dir.$plugin.".pid";
            open FILE, $filename;
            # read the record, and chomp off the newline
            chomp(my $record = <FILE>);
            close FILE;
            #DEBUG sprintf("dmg_snmp.pl : plugin_pid pid = %s", $record);
            $HoH->{ $record } = {
                 'plugin'  => $plugin,
             };
        }
        my $delay = sprintf("%ds", $ttl_pid);
        $cache->set('plugin_pid', $HoH, $delay );
    };
    return $HoH
}

sub compute_version {
    # Compute the version of Domogik
    # Return a string
    my $Version = $cache->get("version");
    if ( !defined $Version ) {
        DEBUG "dmg_snmp.pl : version NOT IN cache";
        my $Command = sprintf("%s -V", $dmg_manager);
        $Version = `$Command` or $Version = "Unknown";
        my $delay = sprintf("%ds", $ttl_python);
        $cache->set('version', $Version, $delay );
    };
    return $Version
}

sub compute_process {
    # Compute the process table
    # Add an item by plugin and one application item.
    # Return an hash of hash
    # (
    # application => {
    #     pcpu  => 0,
    #     pmem  => 0,
    #     rss  => 0,
    #     size  => 0,
    #     count => number_of_running_plugins,
    #     },
    # manager => {
    #     pid   => 0,
    #     pcpu  => 0,
    #     pmem  => 0,
    #     rss  => 0,
    #     size  => 0,
    #     },
    # pluginname => {
    #     ...
    # )
    my $HoH = $cache->get("compute_process");
    if ( !defined $HoH ) {
        DEBUG "dmg_snmp.pl : compute_process NOT IN cache";
        $HoH->{ 'application' } = {
                 'pcpu'  => 0,
                 'pmem'  => 0,
                 'rss'  => 0,
                 'size'  => 0,
                 'startcore' => 0,
                 'enabcore' => 0,
                 'startplug' => 0,
                 'enabplug' => 0,
             };
        my $core_pid = compute_core_pid();
        my @cores = @{compute_core_list()};
        my $core;
        for $core ( @cores ) {
            #DEBUG sprintf("dmg_snmp.pl : compute_process core = %s", $core);
            $HoH->{ $core } = {
                     'pid' => 0,
                     'pcpu'  => 0,
                     'pmem'  => 0,
                     'rss'  => 0,
                     'size'  => 0,
                     'started'  => 0,
                 };
            $HoH->{ 'application' }->{'enabcore'} = $HoH->{ 'application' }->{'enabcore'} + 1;
        }
        my $plugin_pid = compute_plugin_pid();
        my @plugins = @{compute_plugin_list()};
        my $plugin;
        for $plugin ( @plugins ) {
            #DEBUG sprintf("dmg_snmp.pl : compute_process plugin = %s", $plugin);
            $HoH->{ $plugin } = {
                     'pid' => 0,
                     'pcpu'  => 0,
                     'pmem'  => 0,
                     'rss'  => 0,
                     'size'  => 0,
                     'started'  => 0,
                 };
            $HoH->{ 'application' }->{'enabplug'} = $HoH->{ 'application' }->{'enabplug'} + 1;
        }
        my $proc_table = new Proc::ProcessTable;
        my $proc;
        foreach $proc ( @{$proc_table->table} ){
            #DEBUG sprintf("dmg_snmp.pl : compute_process fname = %s", $proc->fname);
            #DEBUG sprintf("dmg_snmp.pl : compute_process pid = %s", $proc->pid);
            #DEBUG sprintf("dmg_snmp.pl : compute_process plugin id = %s", $core_pid->{$proc->pid});
            if( exists $core_pid->{$proc->pid} ) {
                my $plugin_name = $core_pid->{$proc->pid}->{'plugin'};
                $HoH->{ $plugin_name }->{'pid'} = $proc->pid;
                $HoH->{ $plugin_name }->{'pcpu'} = $proc->pctcpu;
                $HoH->{ $plugin_name }->{'pmem'} =  $proc->pctmem;
                $HoH->{ $plugin_name }->{'rss'} =  $proc->rss;
                $HoH->{ $plugin_name }->{'size'} =  $proc->size;
                $HoH->{ $plugin_name }->{'started'} =  1;
                #DEBUG sprintf("dmg_snmp.pl : compute_process fname = %s", $proc->fname);
                $HoH->{ 'application' }->{'pcpu'} = $HoH->{ 'application' }->{'pcpu'} + $proc->pctcpu;
                $HoH->{ 'application' }->{'pmem'} = $HoH->{ 'application' }->{'pmem'} + $proc->pctmem;
                $HoH->{ 'application' }->{'rss'} = $HoH->{ 'application' }->{'rss'} + $proc->rss;
                $HoH->{ 'application' }->{'size'} = $HoH->{ 'application' }->{'size'} + $proc->size;
                $HoH->{ 'application' }->{'startcore'} = $HoH->{ 'application' }->{'startcore'} + 1;
                #DEBUG sprintf("dmg_snmp.pl : compute_process application.pcpu = %s", $HoH->{ 'application' }->{'pcpu'});
                #DEBUG sprintf("dmg_snmp.pl : compute_process application.pmem = %s", $HoH->{ 'application' }->{'pmem'});
                #DEBUG sprintf("dmg_snmp.pl : compute_process application.rss = %s", $HoH->{ 'application' }->{'rss'});
                #DEBUG sprintf("dmg_snmp.pl : compute_process application.size = %s", $HoH->{ 'application' }->{'size'});
            } elsif( exists $plugin_pid->{$proc->pid} ) {
                my $plugin_name = $plugin_pid->{$proc->pid}->{'plugin'};
                $HoH->{ $plugin_name }->{'pid'} = $proc->pid;
                $HoH->{ $plugin_name }->{'pcpu'} = $proc->pctcpu;
                $HoH->{ $plugin_name }->{'pmem'} =  $proc->pctmem;
                $HoH->{ $plugin_name }->{'rss'} =  $proc->rss;
                $HoH->{ $plugin_name }->{'size'} =  $proc->size;
                $HoH->{ $plugin_name }->{'started'} =  1;
                #DEBUG sprintf("dmg_snmp.pl : compute_process fname = %s", $proc->fname);
                $HoH->{ 'application' }->{'pcpu'} = $HoH->{ 'application' }->{'pcpu'} + $proc->pctcpu;
                $HoH->{ 'application' }->{'pmem'} = $HoH->{ 'application' }->{'pmem'} + $proc->pctmem;
                $HoH->{ 'application' }->{'rss'} = $HoH->{ 'application' }->{'rss'} + $proc->rss;
                $HoH->{ 'application' }->{'size'} = $HoH->{ 'application' }->{'size'} + $proc->size;
                $HoH->{ 'application' }->{'startplug'} = $HoH->{ 'application' }->{'startplug'} + 1;
                #DEBUG sprintf("dmg_snmp.pl : compute_process application.pcpu = %s", $HoH->{ 'application' }->{'pcpu'});
                #DEBUG sprintf("dmg_snmp.pl : compute_process application.pmem = %s", $HoH->{ 'application' }->{'pmem'});
                #DEBUG sprintf("dmg_snmp.pl : compute_process application.rss = %s", $HoH->{ 'application' }->{'rss'});
                #DEBUG sprintf("dmg_snmp.pl : compute_process application.size = %s", $HoH->{ 'application' }->{'size'});
            }
        }
        my $delay = sprintf("%ds", $ttl_process);
        $cache->set('compute_process', $HoH, $delay );
    };
    return $HoH
}

sub application_handler {
  # This is the callback used by the SNMP agent
  my ($handler, $registration_info, $request_info, $requests) = @_;
  DEBUG "dmg_snmp.pl : application_handler";
  my $full_oid = $domogik_oid.$sub_oid_application;
  my $request;
  my $HoH = compute_process();
  for($request = $requests; $request; $request = $request->next()) {
    my $oid = $request->getOID();
    if ($request_info->getMode() == MODE_GET) {
      if ($oid == new NetSNMP::OID($full_oid.".0")) {
        # The domogik name
        $request->setValue(ASN_OCTET_STR, "Domogik");
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".1")) {
        # The domogik version
        my $RestInfo = compute_rest_info();
        $request->setValue(ASN_OCTET_STR, $RestInfo->{'version'});
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".2")) {
        # The rest version
        my $RestInfo = compute_rest_info();
        $request->setValue(ASN_OCTET_STR, $RestInfo->{'rest_version'});
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".3")) {
        # The Zmq version
        my $ZmqInfo = compute_zmq_info();
        $request->setValue(ASN_OCTET_STR, $ZmqInfo->{'version'});
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".10.0")) {
        # The number of plugins enabled
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'enabcore'} + $HoH->{'application'}->{'enabplug'});
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".10.1")) {
        # The number of plugins started
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'startcore'} + $HoH->{'application'}->{'startplug'});
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".10.10.0")) {
        # The percentage of cpu use
        $request->setValue(ASN_OCTET_STR, sprintf("%.2f", $HoH->{ 'application' }->{'pcpu'}));
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".10.11.0")) {
        # The percentage of memory use
        $request->setValue(ASN_OCTET_STR, sprintf("%.2f", $HoH->{ 'application' }->{'pmem'}));
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".10.11.1")) {
        # The rss memory use
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'rss'});
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".10.11.2")) {
        # The size memory use
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'size'});
      }
    } elsif ($request_info->getMode() == MODE_GETNEXT) {
      if ($oid == new NetSNMP::OID($full_oid.".0")) {
        $request->setOID($full_oid.".1");
        my $RestInfo = compute_rest_info();
        $request->setValue(ASN_OCTET_STR, $RestInfo->{'version'});
      }
      if ($oid == new NetSNMP::OID($full_oid.".1")) {
        $request->setOID($full_oid.".2");
        my $RestInfo = compute_rest_info();
        $request->setValue(ASN_OCTET_STR, $RestInfo->{'rest_version'});
      }
      if ($oid == new NetSNMP::OID($full_oid.".2")) {
        $request->setOID($full_oid.".3");
        my $ZmqInfo = compute_zmq_info();
        $request->setValue(ASN_OCTET_STR, $ZmqInfo->{'version'});
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".3")) {
        $request->setOID($full_oid.".10.0");
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'enabcore'} + $HoH->{'application'}->{'enabplug'});
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".10.0")) {
        $request->setOID($full_oid.".10.1");
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'startcore'} + $HoH->{'application'}->{'startplug'});
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".10.1")) {
        $request->setOID($full_oid.".10.10.0");
        $request->setValue(ASN_OCTET_STR, sprintf("%.2f", $HoH->{ 'application' }->{'pcpu'}));
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".10.10.0")) {
        $request->setOID($full_oid.".10.11.0");
        $request->setValue(ASN_OCTET_STR, sprintf("%.2f", $HoH->{ 'application' }->{'pmem'}));
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".10.11.0")) {
        $request->setOID($full_oid.".10.11.1");
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'rss'});
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".10.11.1")) {
        $request->setOID($full_oid.".10.11.2");
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'size'});
      }
      elsif ($oid < new NetSNMP::OID($full_oid.".0")) {
        $request->setOID($full_oid.".0");
        $request->setValue(ASN_OCTET_STR, "Domogik");
      }
    }
  }
}

sub core_handler {
  # This is the callback used by the SNMP agent
  my ($handler, $registration_info, $request_info, $requests) = @_;
  DEBUG "dmg_snmp.pl : application_handler";
  my $full_oid = $domogik_oid.$sub_oid_core;
  my $request;
  my $HoH = compute_process();
  for($request = $requests; $request; $request = $request->next()) {
    my $oid = $request->getOID();
    if ($request_info->getMode() == MODE_GET) {
      if ($oid == new NetSNMP::OID($full_oid.".0")) {
        # The number of plugins enabled
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'enabcore'});
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".1")) {
        # The number of plugins started
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'startcore'});
      }
    } elsif ($request_info->getMode() == MODE_GETNEXT) {
      if ($oid == new NetSNMP::OID($full_oid.".0")) {
        $request->setOID($full_oid.".1");
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'startcore'});
      }
      elsif ($oid < new NetSNMP::OID($full_oid.".0")) {
        $request->setOID($full_oid.".0");
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'enabcore'});
      }
    }
  }
}

sub core_plugin_handler {
  # This is the callback used by the SNMP agent for the core plugin
  # It must retrieve a plugin using its OID
  my ($handler, $registration_info, $request_info, $requests) = @_;
  #DEBUG sprintf("dmg_snmp.pl : core_handler registration_info = %s", $registration_info->getRootOID());
  my $oid = $registration_info->getRootOID();
  my $CoreOrder = compute_core_order();
  my $plugin_oid;
  my $plugin_name;
  my $core;
  foreach $core ( keys %$CoreOrder ) {
    my $first_oid = $domogik_oid.$CoreOrder->{ $core }->{ "firstoid" };
    #my $next_oid = $domogik_oid.$CoreOrder->{ $core }->{ "nextoid" };
    if ($oid == new NetSNMP::OID($first_oid)) {
        $plugin_oid = $first_oid;
        $plugin_name = $CoreOrder->{ $core }->{ "plugin" };
        #DEBUG sprintf("dmg_snmp.pl : core_handler first_oid = %s", $first_oid);
        #DEBUG sprintf("dmg_snmp.pl : core_handler plugin_name = %s", $plugin_name);
        #DEBUG sprintf("dmg_snmp.pl : core_handler core = %s", $CoreOrder->{ $core });
        last;
        };
    };
  #DEBUG sprintf("dmg_snmp.pl : core_handler full_oid = %s", $full_oid);
  #DEBUG sprintf("dmg_snmp.pl : core_handler plugin_name = %s", $plugin_name);
  #plugin_core_handler($plugin_name, $full_oid, $handler, $registration_info, $request_info, $requests);
  my $request;
  my $HoH = compute_process();
  DEBUG sprintf("dmg_snmp.pl : plugin_handler plugin = %s", $plugin_name);
  for($request = $requests; $request; $request = $request->next()) {
    my $oid = $request->getOID();
    if ($request_info->getMode() == MODE_GET) {
      if ($oid == new NetSNMP::OID($plugin_oid.".0")) {
        # The plugin name
        $request->setValue(ASN_OCTET_STR, $plugin_name);
      }
      elsif ($oid == new NetSNMP::OID($plugin_oid.".1")) {
        # The plugin pid
        $request->setValue(ASN_INTEGER, $HoH->{ $plugin_name }->{'pid'});
      }
      elsif ($oid == new NetSNMP::OID($plugin_oid.".10.0")) {
        # The percentage of cpu use
        $request->setValue(ASN_OCTET_STR, sprintf("%.2f", $HoH->{ $plugin_name }->{'pcpu'}));
      }
      elsif ($oid == new NetSNMP::OID($plugin_oid.".11.0")) {
        # The percentage of memory use
        $request->setValue(ASN_OCTET_STR, sprintf("%.2f", $HoH->{ $plugin_name }->{'pmem'}));
      }
      elsif ($oid == new NetSNMP::OID($plugin_oid.".11.1")) {
        # The rss memory use
        $request->setValue(ASN_INTEGER, $HoH->{$plugin_name}->{'rss'});
      }
      elsif ($oid == new NetSNMP::OID($plugin_oid.".11.2")) {
        # The size memory use
        $request->setValue(ASN_INTEGER, $HoH->{$plugin_name}->{'size'});
      }
    } elsif ($request_info->getMode() == MODE_GETNEXT) {
      if ($oid == new NetSNMP::OID($plugin_oid.".0")) {
        $request->setOID($plugin_oid.".1");
        $request->setValue(ASN_INTEGER, $HoH->{ $plugin_name }->{'pid'});
      }
      elsif ($oid == new NetSNMP::OID($plugin_oid.".1")) {
        $request->setOID($plugin_oid.".10.0");
        $request->setValue(ASN_OCTET_STR, sprintf("%.2f", $HoH->{ $plugin_name }->{'pcpu'}));
      }
      elsif ($oid == new NetSNMP::OID($plugin_oid.".10.0")) {
        $request->setOID($plugin_oid.".11.0");
        $request->setValue(ASN_OCTET_STR, sprintf("%.2f", $HoH->{ $plugin_name }->{'pmem'}));
      }
      elsif ($oid == new NetSNMP::OID($plugin_oid.".11.0")) {
        $request->setOID($plugin_oid.".11.1");
        $request->setValue(ASN_INTEGER, $HoH->{$plugin_name}->{'rss'});
      }
      elsif ($oid == new NetSNMP::OID($plugin_oid.".11.1")) {
        $request->setOID($plugin_oid.".11.2");
        $request->setValue(ASN_INTEGER, $HoH->{$plugin_name}->{'size'});
      }
      elsif ($oid < new NetSNMP::OID($plugin_oid.".0")) {
        $request->setOID($plugin_oid.".0");
        $request->setValue(ASN_OCTET_STR, $plugin_name);
      }
    }
  }
}

sub plugins_handler {
  # Plugins handler
  my ($handler, $registration_info, $request_info, $requests) = @_;
  my $request;
  my $full_oid = $domogik_oid.$sub_oid_plugins;
  my $HoH = compute_process();
  DEBUG sprintf("dmg_snmp.pl : plugins_handler ");
  for($request = $requests; $request; $request = $request->next()) {
    my $oid = $request->getOID();
    if ($request_info->getMode() == MODE_GET) {
      if ($oid == new NetSNMP::OID($full_oid.".0")) {
        # The number of plugins enabled
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'enabplug'});
      }
      elsif ($oid == new NetSNMP::OID($full_oid.".1")) {
        # The number of plugins started
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'startplug'});
      }
    } elsif ($request_info->getMode() == MODE_GETNEXT) {
      if ($oid == new NetSNMP::OID($full_oid.".0")) {
        $request->setOID($full_oid.".1");
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'startplug'});
      }
      elsif ($oid < new NetSNMP::OID($full_oid.".0")) {
        $request->setOID($full_oid.".0");
        $request->setValue(ASN_INTEGER, $HoH->{'application'}->{'enabplug'});
      }
    }
  }
}

sub plugins_name_handler {
  # Plugins handler
  my ($handler, $registration_info, $request_info, $requests) = @_;
  my $request;
  my $full_oid = $domogik_oid.$sub_oid_plugins.$oid_plugins_name;
  my $HoH = compute_process();
  #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler ");
  for($request = $requests; $request; $request = $request->next()) {
    my $oid = $request->getOID();
    # The name the plugins
    my $plugins = compute_plugin_list();
    my @arrayref = $oid->to_array();
    #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler last arrayref = %s",$arrayref[-1]);
    #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler oid = %s",$oid);
    my $last = $arrayref[-1];
    my $size = @$plugins;
    if ($request_info->getMode() == MODE_GET) {
        if ( ( exists $plugins->[$last] ) and ( $oid > $registration_info->getRootOID())) {
#        if ($last < $size) {
            $request->setValue(ASN_OCTET_STR, @$plugins[$last]);
        }
    } elsif ($request_info->getMode() == MODE_GETNEXT) {
        # The name the plugins
        if ($oid < new NetSNMP::OID($full_oid.".0")) {
            $request->setOID($full_oid.".0");
            $request->setValue(ASN_OCTET_STR, @$plugins[0]);
        } else {
            if( exists $plugins->[$last+1] ) {
#            if ($last < $size) {
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler last < size");
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler last+1 = %s",$last+1);
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler plugins[last+1] = %s",@$plugins[$last+1]);
                my $ch = sprintf(".%d",$last+1);
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler ch = %s",$ch);
                $request->setOID($full_oid.$ch);
                $request->setValue(ASN_OCTET_STR, @$plugins[$last+1]);
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler newoid = %s",$full_oid.$ch);
            }
        }
      }
    }
  }

sub plugins_started_handler {
  # Plugins handler
  my ($handler, $registration_info, $request_info, $requests) = @_;
  my $request;
  my $full_oid = $domogik_oid.$sub_oid_plugins.$oid_plugins_started;
  my $HoH = compute_process();
  #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler ");
  for($request = $requests; $request; $request = $request->next()) {
    my $oid = $request->getOID();
    # The name the plugins
    my $plugins = compute_plugin_list();
    my @arrayref = $oid->to_array();
    #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler last arrayref = %s",$arrayref[-1]);
    #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler oid = %s",$oid);
    my $last = $arrayref[-1];
    my $size = @$plugins;
    if ($request_info->getMode() == MODE_GET) {
        if ( ( exists $plugins->[$last] ) and ( $oid > $registration_info->getRootOID())) {
#        if ($last < $size) {
            $request->setValue(ASN_INTEGER, $HoH->{@$plugins[$last]}->{'started'});
        }
    } elsif ($request_info->getMode() == MODE_GETNEXT) {
        # The name the plugins
        if ($oid < new NetSNMP::OID($full_oid.".0")) {
            $request->setOID($full_oid.".0");
            $request->setValue(ASN_INTEGER, $HoH->{@$plugins[0]}->{'started'});
        } else {
            if( exists $plugins->[$last+1] ) {
#            if ($last < $size) {
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler last < size");
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler last+1 = %s",$last+1);
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler plugins[last+1] = %s",@$plugins[$last+1]);
                my $ch = sprintf(".%d",$last+1);
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler ch = %s",$ch);
                $request->setOID($full_oid.$ch);
                $request->setValue(ASN_INTEGER, $HoH->{@$plugins[$last+1]}->{'started'});
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler newoid = %s",$full_oid.$ch);
            }
        }
      }
    }
  }

sub plugins_pid_handler {
  # Plugins handler
  my ($handler, $registration_info, $request_info, $requests) = @_;
  my $request;
  my $full_oid = $domogik_oid.$sub_oid_plugins.$oid_plugins_pid;
  my $HoH = compute_process();
  #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler ");
  for($request = $requests; $request; $request = $request->next()) {
    my $oid = $request->getOID();
    # The name the plugins
    my $plugins = compute_plugin_list();
    my @arrayref = $oid->to_array();
    #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler last arrayref = %s",$arrayref[-1]);
    #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler oid = %s",$oid);
    my $last = $arrayref[-1];
    my $size = @$plugins;
    if ($request_info->getMode() == MODE_GET) {
        if ( ( exists $plugins->[$last] ) and ( $oid > $registration_info->getRootOID())) {
#        if ($last < $size) {
            $request->setValue(ASN_INTEGER, $HoH->{@$plugins[$last]}->{'pid'});
        }
    } elsif ($request_info->getMode() == MODE_GETNEXT) {
        # The name the plugins
        if ($oid < new NetSNMP::OID($full_oid.".0")) {
            $request->setOID($full_oid.".0");
            $request->setValue(ASN_INTEGER, $HoH->{@$plugins[0]}->{'pid'});
        } else {
            if( exists $plugins->[$last+1] ) {
#            if ($last < $size) {
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler last < size");
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler last+1 = %s",$last+1);
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler plugins[last+1] = %s",@$plugins[$last+1]);
                my $ch = sprintf(".%d",$last+1);
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler ch = %s",$ch);
                $request->setOID($full_oid.$ch);
                $request->setValue(ASN_INTEGER, $HoH->{@$plugins[$last+1]}->{'pid'});
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler newoid = %s",$full_oid.$ch);
            }
        }
      }
    }
  }

sub plugins_pcpu_handler {
  # Plugins handler
  my ($handler, $registration_info, $request_info, $requests) = @_;
  my $request;
  my $full_oid = $domogik_oid.$sub_oid_plugins.$oid_plugins_pcpu;
  my $HoH = compute_process();
  #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler ");
  for($request = $requests; $request; $request = $request->next()) {
    my $oid = $request->getOID();
    # The name the plugins
    my $plugins = compute_plugin_list();
    my @arrayref = $oid->to_array();
    #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler last arrayref = %s",$arrayref[-1]);
    #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler oid = %s",$oid);
    my $last = $arrayref[-1];
    my $size = @$plugins;
    if ($request_info->getMode() == MODE_GET) {
        if ( ( exists $plugins->[$last] ) and ( $oid > $registration_info->getRootOID())) {
#        if ($last < $size) {
            $request->setValue(ASN_OCTET_STR, sprintf("%.2f", $HoH->{@$plugins[$last]}->{'pcpu'}));
        }
    } elsif ($request_info->getMode() == MODE_GETNEXT) {
        # The name the plugins
        if ($oid < new NetSNMP::OID($full_oid.".0")) {
            $request->setOID($full_oid.".0");
            $request->setValue(ASN_OCTET_STR, sprintf("%.2f", $HoH->{@$plugins[0]}->{'pcpu'}));
        } else {
            if( exists $plugins->[$last+1] ) {
#            if ($last < $size) {
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler last < size");
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler last+1 = %s",$last+1);
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler plugins[last+1] = %s",@$plugins[$last+1]);
                my $ch = sprintf(".%d",$last+1);
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler ch = %s",$ch);
                $request->setOID($full_oid.$ch);
                $request->setValue(ASN_OCTET_STR, sprintf("%.2f", $HoH->{@$plugins[$last+1]}->{'pcpu'}));
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler newoid = %s",$full_oid.$ch);
            }
        }
      }
    }
  }

sub plugins_pmem_handler {
  # Plugins handler
  my ($handler, $registration_info, $request_info, $requests) = @_;
  my $request;
  my $full_oid = $domogik_oid.$sub_oid_plugins.$oid_plugins_pmem;
  my $HoH = compute_process();
  #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler ");
  for($request = $requests; $request; $request = $request->next()) {
    my $oid = $request->getOID();
    # The name the plugins
    my $plugins = compute_plugin_list();
    my @arrayref = $oid->to_array();
    #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler last arrayref = %s",$arrayref[-1]);
    #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler oid = %s",$oid);
    my $last = $arrayref[-1];
    my $size = @$plugins;
    if ($request_info->getMode() == MODE_GET) {
        if ( ( exists $plugins->[$last] ) and ( $oid > $registration_info->getRootOID())) {
#        if ($last < $size) {
            $request->setValue(ASN_OCTET_STR, sprintf("%.2f", $HoH->{@$plugins[$last]}->{'pmem'}));
        }
    } elsif ($request_info->getMode() == MODE_GETNEXT) {
        # The name the plugins
        if ($oid < new NetSNMP::OID($full_oid.".0")) {
            $request->setOID($full_oid.".0");
            $request->setValue(ASN_OCTET_STR, sprintf("%.2f", $HoH->{@$plugins[0]}->{'pmem'}));
        } else {
            if( exists $plugins->[$last+1] ) {
#            if ($last < $size) {
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler last < size");
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler last+1 = %s",$last+1);
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler plugins[last+1] = %s",@$plugins[$last+1]);
                my $ch = sprintf(".%d",$last+1);
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler ch = %s",$ch);
                $request->setOID($full_oid.$ch);
                $request->setValue(ASN_OCTET_STR, sprintf("%.2f", $HoH->{@$plugins[$last+1]}->{'pmem'}));
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler newoid = %s",$full_oid.$ch);
            }
        }
      }
    }
  }

sub plugins_rss_handler {
  # Plugins handler
  my ($handler, $registration_info, $request_info, $requests) = @_;
  my $request;
  my $full_oid = $domogik_oid.$sub_oid_plugins.$oid_plugins_rss;
  my $HoH = compute_process();
  #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler ");
  for($request = $requests; $request; $request = $request->next()) {
    my $oid = $request->getOID();
    # The name the plugins
    my $plugins = compute_plugin_list();
    my @arrayref = $oid->to_array();
    #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler last arrayref = %s",$arrayref[-1]);
    #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler oid = %s",$oid);
    my $last = $arrayref[-1];
    my $size = @$plugins;
    if ($request_info->getMode() == MODE_GET) {
        if ( ( exists $plugins->[$last] ) and ( $oid > $registration_info->getRootOID())) {
#        if ($last < $size) {
            $request->setValue(ASN_INTEGER, $HoH->{@$plugins[$last]}->{'rss'});
        }
    } elsif ($request_info->getMode() == MODE_GETNEXT) {
        # The name the plugins
        if ($oid < new NetSNMP::OID($full_oid.".0")) {
            $request->setOID($full_oid.".0");
            $request->setValue(ASN_INTEGER, $HoH->{@$plugins[0]}->{'rss'});
        } else {
            if( exists $plugins->[$last+1] ) {
#            if ($last < $size) {
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler last < size");
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler last+1 = %s",$last+1);
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler plugins[last+1] = %s",@$plugins[$last+1]);
                my $ch = sprintf(".%d",$last+1);
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler ch = %s",$ch);
                $request->setOID($full_oid.$ch);
                $request->setValue(ASN_INTEGER, $HoH->{@$plugins[$last+1]}->{'rss'});
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler newoid = %s",$full_oid.$ch);
            }
        }
      }
    }
  }

sub plugins_size_handler {
  # Plugins handler
  my ($handler, $registration_info, $request_info, $requests) = @_;
  my $request;
  my $full_oid = $domogik_oid.$sub_oid_plugins.$oid_plugins_size;
  my $HoH = compute_process();
  #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler ");
  for($request = $requests; $request; $request = $request->next()) {
    my $oid = $request->getOID();
    # The name the plugins
    my $plugins = compute_plugin_list();
    my @arrayref = $oid->to_array();
    #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler last arrayref = %s",$arrayref[-1]);
    #DEBUG sprintf("dmg_snmp.pl : plugins_name_handler oid = %s",$oid);
    my $last = $arrayref[-1];
    my $size = @$plugins;
    if ($request_info->getMode() == MODE_GET) {
        if ( ( exists $plugins->[$last] ) and ( $oid > $registration_info->getRootOID())) {
#        if ($last < $size) {
            $request->setValue(ASN_INTEGER, $HoH->{@$plugins[$last]}->{'size'});
        }
    } elsif ($request_info->getMode() == MODE_GETNEXT) {
        # The name the plugins
        if ($oid < new NetSNMP::OID($full_oid.".0")) {
            $request->setOID($full_oid.".0");
            $request->setValue(ASN_INTEGER, $HoH->{@$plugins[0]}->{'size'});
        } else {
            if( exists $plugins->[$last+1] ) {
#            if ($last < $size) {
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler last < size");
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler last+1 = %s",$last+1);
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler plugins[last+1] = %s",@$plugins[$last+1]);
                my $ch = sprintf(".%d",$last+1);
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler ch = %s",$ch);
                $request->setOID($full_oid.$ch);
                $request->setValue(ASN_INTEGER, $HoH->{@$plugins[$last+1]}->{'size'});
                #DEBUG sprintf("dmg_snmp.pl : plugins_handler newoid = %s",$full_oid.$ch);
            }
        }
      }
    }
  }

sub init_parameters {
    # Load parameters from configuration file.
    # following new() always returns true:
    DEBUG "dmg_snmp.pl : init parameters ";
    my $cfg = new Config::Simple();
    # read() can fail:
    $cfg->read($configuration_file) or die $cfg->error();
    my $Config = $cfg->vars();
    $ttl_process = $Config->{'ttl.process'};
    $ttl_rest = $Config->{'ttl.rest'};
    $ttl_python = $Config->{'ttl.python'};
    $ttl_conf = $Config->{'ttl.conf'};
    $ttl_zmq = $Config->{'ttl.zmq'};
    $domogik_cfg = $Config->{'domogik.config'};
    $dmg_manager = $Config->{'domogik.manager'};
    $debug = $Config->{'snmp.debug'};

    my $cfg2 = new Config::Simple();
    $cfg2->read($domogik_cfg) or die $cfg2->error();
    my $Config2 = $cfg2->vars();
    $domogik_pid_dir = $Config2->{'domogik.pid_dir_path'};
    $rest_ip = $Config2->{'rest.rest_server_ip'};
    $rest_port = $Config2->{'rest.rest_server_port'};
    if ( $debug == 1 ) {
        Log::Log4perl->easy_init($DEBUG);
    } else {
        Log::Log4perl->easy_init($INFO);
    }
}

DEBUG "dmg_snmp.pl : start ... ";
# We define a cache to retrieve values
# Some values are requested many times in a short time (snmpwalk use getnext)
# So I a good idea to cache them
# We define a 2 Level cache : in a file with L1 cache in memory (1024 * 1024 bytes)
DEBUG "dmg_snmp.pl : init cache";
$cache = CHI->new(
        driver   => 'File',
        root_dir => '/tmp/dmg_snmp.cache',
        l1_cache => { driver => 'Memory', global => 1, max_size => 1024*1024 }
    );

#DEBUG "dmg_snmp.pl : init ZMQ";
#$zmq_context = zmq_init();

# Init the parameters
init_parameters();
# Create the agent
DEBUG "dmg_snmp.pl : create agent";
$agent = new NetSNMP::agent();
# Register the application part
DEBUG "dmg_snmp.pl : register application part";
#$agent->register("hello_world", ".1.3.6.1.4.1.8072.9999.9999",
#                 \&hello_handler);
$agent->register("application", $domogik_oid.$sub_oid_application,
                  \&application_handler);
# Register the core part
$agent->register("core", $domogik_oid.$sub_oid_core,
        \&core_handler);
# Register the plugins part
$agent->register("plugins", $domogik_oid.$sub_oid_plugins,
        \&plugins_handler);
# Register the plugins names part
$agent->register("plugins_name", $domogik_oid.$sub_oid_plugins.$oid_plugins_name,
        \&plugins_name_handler);
# Register the plugins started part
$agent->register("plugins_started", $domogik_oid.$sub_oid_plugins.$oid_plugins_started,
        \&plugins_started_handler);
# Register the plugins pid part
$agent->register("plugins_pid", $domogik_oid.$sub_oid_plugins.$oid_plugins_pid,
        \&plugins_pid_handler);
# Register the plugins pcpu part
$agent->register("plugins_pcpu", $domogik_oid.$sub_oid_plugins.$oid_plugins_pcpu,
        \&plugins_pcpu_handler);
# Register the plugins pmem part
$agent->register("plugins_pmem", $domogik_oid.$sub_oid_plugins.$oid_plugins_pmem,
        \&plugins_pmem_handler);
# Register the plugins rss part
$agent->register("plugins_rss", $domogik_oid.$sub_oid_plugins.$oid_plugins_rss,
        \&plugins_rss_handler);
# Register the plugins size part
$agent->register("plugins_size", $domogik_oid.$sub_oid_plugins.$oid_plugins_size,
        \&plugins_size_handler);

my $CoreOrder = compute_core_order();
my $core;
foreach $core ( sort keys %$CoreOrder ) {
    DEBUG sprintf("dmg_snmp.pl : register %s", $CoreOrder->{ $core }->{ 'plugin' });
    DEBUG sprintf("dmg_snmp.pl : at %s", $CoreOrder->{ $core }->{ 'firstoid' });
    $agent->register($CoreOrder->{ $core }->{ 'plugin' }, $domogik_oid.$CoreOrder->{ $core }->{ 'firstoid' },
            \&core_plugin_handler);
    };

INFO "dmg_snmp.pl started";

1;
