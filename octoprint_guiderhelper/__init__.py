# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin
import socket
import threading
import time
import re
import logging

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin

class GuiderHelperPlugin(octoprint.plugin.StartupPlugin, 
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin
):
    hosts=""
    port=4422
    commands = list()
    connected = True

    def __init__(self):
        self.host="",
        self.port=4422,
        self.connected=True

    def socket_daemon(self):
        while True:
            time.sleep(0.25)
            if len(self.commands):
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.connect((self.host, self.port))
                except Exception as e:
                    if self.connected is True:
                      self.connected = False
                      self._logger.error("something's wrong. Exception is %s" % (e))
                else:
                    self.connected = True
                    cmd = self.commands.pop(0)
                    s.sendall(cmd.encode('utf-8'))
                    self._logger.info("Sending: %s'" % (cmd))
                    time.sleep(0.1)
                finally:
                    s.close()

    def sendTcp(self, command):
        if self.host != "" and self.port != 0 and self.connected is True:
            self._logger.info("Queuing command: %s'" % (command))
            self.commands.append(command.replace("// ",""))

    def on_after_startup(self):
        self.get_settings_updates()
        self._logger.info("\nGuiderIIs (at: %s:%d)\n" % (self._settings.get(["host"]),self._settings.get(["port"])))
        thread = threading.Thread(target=self.socket_daemon)
        thread.daemon = True
        thread.start()
    
    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            host="",
            port=4422,
        )

    def on_settings_save(self, data):
        s = self._settings
        if "host" in list(data.keys()):
            s.set(["host"], data["host"])
        if "port" in list(data.keys()):
            s.set_int(["port"], data["port"])
        self.get_settings_updates()
        #clean up settings if everything's default
        self.on_settings_cleanup()
        s.save()

    def get_template_vars(self):
        return dict(host=self._settings.get(["host"]),port=self._settings.get_int(["port"]))

    def get_settings_updates(self):
        self.host = self._settings.get(["host"])
        self.port = self._settings.get_int(["port"])

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def sent_gcode(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if gcode:
            if gcode.startswith("M117"):
                self.sendTcp(cmd)
            elif gcode.startswith("M118"):
                self.sendTcp(cmd)
            elif gcode.startswith("M300"):
                self.sendTcp(cmd)
        return cmd
    
    def received_gcode(self, comm, line, *args, **kwargs):
        if ( not line or line == "ok" ):
            return
        
        if line.startswith("M117"):
            self.sendTcp(line)
        elif line.startswith("M118"):
            self.sendTcp(line)
        elif line.startswith("M300"):
            self.sendTcp(line)
        elif line.startswith("// gcode"):
            self.sendTcp(line)
        return line
      
    def error_gcode(self, comm, error_message, *args, **kwargs):
        if ( not error_message or error_message == "ok" ):
            return
        
        self.sendTcp("Error: " + error_message)
        return False

    def actioncommand(self, comm, line, command, *args, **kwargs):
        if command == None:
            return
        if command.startswith('prompt'):
            self.sendTcp(command)
        else:
            self.sendTcp(command)


    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": ["js/guiderhelper.js"],
            "css": ["css/guiderhelper.css"],
            "less": ["less/guiderhelper.less"]
        }

    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "guiderhelper": {
                "displayName": "GuiderHelper Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "Pavulon87",
                "repo": "OctoPrint-GuiderHelper",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/Pavulon87/OctoPrint-GuiderHelper/archive/{target_version}.zip",
            }
        }


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "GuiderHelper Plugin"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
#__plugin_pythoncompat__ = ">=2.7,<3" # only python 2
#__plugin_pythoncompat__ = ">=3,<4" # only python 3
__plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = GuiderHelperPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.comm.protocol.action": __plugin_implementation__.actioncommand, 
        "octoprint.comm.protocol.gcode.received": __plugin_implementation__.received_gcode,
        "octoprint.comm.protocol.gcode.error": __plugin_implementation__.error_gcode,
        #"octoprint.comm.protocol.gcode.sent": __plugin_implementation__.sent_gcode,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
