#!/usr/bin/python
#
# dtc_reader.py
#
# Copyright (C) Ben Van Mechelen 2007-2011 <me@benvm.be>
# 
# This file is part of Garmon 
# 
# Garmon is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#   The Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor
#   Boston, MA  02110-1301, USA.

import os

import gobject
from gobject import GObject
import gtk

import garmon
import garmon.plugin

from garmon.plugin import Plugin, STATUS_STOP, STATUS_WORKING, STATUS_PAUSE
from garmon.utils import PropertyObject, gproperty
from garmon.device import OBDDataError, OBDPortError
from garmon.trouble_codes import DTC_CODES, DTC_CODE_CLASSES
from garmon.sensor import decode_dtc_code

__name = _('DTC Reader')
__version = garmon.version
__author = 'Ben Van Mechelen'
__description = _('Reads the stored trouble codes from the vehicle')
__class = 'DTCReader'


(
    COLUMN_CODE,
    COLUMN_DTC,
    COLUMN_DESC
) = range(3)


class DTCReader (gtk.VBox, Plugin):
    __gtype_name__='DTCReader'
    def __init__(self, app):
        gtk.VBox.__init__(self)
        Plugin.__init__(self)
        
        self.app = app
        self.dir = os.path.dirname(__file__)
        self.status = STATUS_STOP
        
        fname = os.path.join(self.dir, 'dtc_reader.ui')
        self._builder = gtk.Builder()
        self._builder.set_translation_domain('garmon')
        self._builder.add_from_file(fname)

        self._dtc_info = DTCInfo(self._builder)
        
        button = self._builder.get_object('re-read-button')
        button.connect('clicked', self._reread_button_clicked)
        
        hpaned = self._builder.get_object('hpaned')
        self.pack_start(hpaned, True, True)
        hpaned.set_border_width(5)

        dtc_frame = self._builder.get_object('dtc_frame')


        self.treemodel = gtk.ListStore(gobject.TYPE_STRING,
                                                        gobject.TYPE_STRING,
                                                        gobject.TYPE_STRING)
        treeview = gtk.TreeView(self.treemodel)
        treeview.set_rules_hint(True)
        #column = gtk.TreeViewColumn(_('Bits'), gtk.CellRendererText(),
        #                            text=COLUMN_CODE)
        #treeview.append_column(column)
        column = gtk.TreeViewColumn(_('DTC'), gtk.CellRendererText(),
                                    text=COLUMN_DTC)
        treeview.append_column(column)
        
        selection = treeview.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)
        selection.connect("changed", self._on_selection_changed)

        dtc_frame.add(treeview)
        
        self.show_all()
        
        self._reset_cbid = app.connect("reset", self._on_reset)
        self._switch_cbid = app.notebook.connect('switch-page', 
                                              self._notebook_page_change_cb)
        

    def _on_reset(self, app):
        if app.device.connected:
            self.start()
        

    def _on_selection_changed(self, selection):
        treeview = selection.get_tree_view()
        model, iter = selection.get_selected()
        
        if iter:
            dtc = model.get_value(iter, COLUMN_DTC)
            cls = DTC_CODE_CLASSES[dtc[:3]]
            description = DTC_CODES[dtc]
            additional = 'Coming soon'
        else:
            dtc = cls = description = additional = ''
            
        self._dtc_info.code = dtc
        self._dtc_info.code_class = cls
        self._dtc_info.description = description
        self._dtc_info.additional = additional


    def _notebook_page_change_cb (self, notebook, no_use, page):
        plugin = notebook.get_nth_page(page)
        if plugin is self:
            self._on_reset(self.app)


    def _reread_button_clicked(self, button):
        self.start()


    def stop(self):
        pass
        

    def start(self):
        def success_cb(cmd, dtcs, args):
            self.treemodel.clear()
            for code in dtcs:
                dtc = decode_dtc_code(code)
                desc = DTC_CODES[dtc]
                iter = self.treemodel.append(None)
                self.treemodel.set(iter, COLUMN_CODE, code,
                                         COLUMN_DTC, dtc,
                                         COLUMN_DESC, desc)  
        
        def error_cb(cmd, error, args):
            self._display_port_error_dialog(error)             

        self.app.queue.stop()
        try:
            self.app.device.read_dtc(success_cb, error_cb)
        except OBDPortError, e:
            self._display_port_error_dialog(e)
            

    def load(self):
        self.app.notebook.append_page(self, gtk.Label(_('DTC Reader')))
                
                
    def unload(self):
        self.app.notebook.disconnect(self._switch_cbid)    
        self.app.disconnect(self._reset_cbid)
        self.app.notebook.remove(self)
        

class DTCInfo(GObject, PropertyObject) :


    gproperty('code', str)
    gproperty('code-class', str)
    gproperty('description', str)
    gproperty('additional', str)


    def __init__(self, builder):
        GObject.__init__(self)
        PropertyObject.__init__(self)

        self._code_label = builder.get_object('code_label')
        self._class_label = builder.get_object('class_label')
        self._description_label = builder.get_object('description_label')
        self._additional_textview = builder.get_object('additional_textview')
    
        self._additional_buffer = gtk.TextBuffer()
        self._additional_textview.set_buffer(self._additional_buffer)

    def __post_init__(self):
        self.connect('notify::code', self._notify_cb)
        self.connect('notify::code-class', self._notify_cb)
        self.connect('notify::description', self._notify_cb)
        self.connect('notify::additional', self._notify_cb)
        
        
    def _notify_cb(self, o, pspec):
        if pspec.name == 'code':
            self._code_label.set_text(self.code)
        elif pspec.name == 'code-class':
            self._class_label.set_text(self.code_class)
        elif pspec.name == 'description':
            self._description_label.set_text(self.description)
        elif pspec.name == 'additional':
            self._additional_buffer.set_text(self.additional)
        
