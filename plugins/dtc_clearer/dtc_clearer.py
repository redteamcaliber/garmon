#!/usr/bin/python
#
# dtc_clearer.py
#
# Copyright (C) Ben Van Mechelen 2007 <me@benvm.be>
# 
# dtc_clearer.py is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor Boston, MA 02110-1301,  USA

from gettext import gettext as _

import gobject
import gtk

import garmon
from garmon.plugin import Plugin

__name = _('DTC Clearer')
__version = '0.1'
__author = 'Ben Van Mechelen'
__description = _('Clears the stored trouble codes in the vehicle')
__class = 'DTCClearer'




class DTCClearer (Plugin):

    def __init__(self, app):

        self.app = app
                
        self.ui_info = '''<ui>
                                <menubar name='MenuBar'>
                                    <menu action='DeviceMenu'>
                                        <placeholder name='DeviceMenuItems'>
                                            <menuitem action='ClearDTC'/>
                                        </placeholder>
                                    </menu>
                                </menubar>
                                <toolbar  name='ToolBar'>
                                    <placeholder name='DeviceToolItems'>
                                    <separator/>
                                        <toolitem action='ClearDTC'/>
                                    </placeholder>
                                </toolbar>
                            </ui>'''
                            
        self._create_action_group()
        

    def _sensitize_action(self):
        sensitive = self.app.obd.connected and not self.app.scheduler.working
        self.app.ui.get_widget('/ToolBar/DeviceToolItems/ClearDTC').set_sensitive(sensitive)
        self.app.ui.get_widget('/MenuBar/DeviceMenu/DeviceMenuItems/ClearDTC').set_sensitive(sensitive)
        

    def _scheduler_notify_working_cb(self, scheduler, monitoring):
        self._sensitize_action()
        
        
    def _obd_connected_cb(self, obd, connected):
        self._sensitize_action()
        
        
    def _create_action_group(self):
        
        entries = (
            ( 'ClearDTC', gtk.STOCK_CLEAR,                     
                _('_Clear DTC'), '',                    
                _('Clear stored trouble codes'), self.activate_clear_dtc ),)
            
        self.action_group = gtk.ActionGroup("ClearDTCActionGroup")
        self.action_group.add_actions(entries)
        
        
        
        
    def activate_clear_dtc(self, action):
        dialog = gtk.MessageDialog(self.app, gtk.DIALOG_DESTROY_WITH_PARENT,
                 gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL,
                 _("""Are You Sure You want to clear the trouble codes?
                
    This will reset the Malfunction Indicator Light.
    Besides that it will also:

     - reset the number of trouble codes
     - erase any diagnostic trouble codes
     - erase any stored freeze frame data
     - erase the DTC that initiated the freeze frame
     - erase all oxygen sensor test data
     - erase mode 06 and 07 information

    Your vehicle may run poorly for a short period of time,
    while it performs a recalibration."""))
            
        dialog.show()
        res = dialog.run()
        dialog.destroy()
        if res == gtk.RESPONSE_OK:
            try:
                self.app.obd.clear_dtc()
                self.app.reset()
            except:
                dialog = gtk.MessageDialog(self.app, gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, 
                    _("An error occurred while trying to reset the dtc.\n\nPlease make sure your device is connected"))
                dialog.run()
                dialog.destroy()
                raise

                
    def load(self):
        self._sensitize_action()
        self.app.scheduler.connect('notify::working', self._scheduler_notify_working_cb)
        self.app.obd.connect('connected', self._obd_connected_cb)
                
                