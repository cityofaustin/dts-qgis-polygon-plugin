# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PolygonizerDockWidget
                                A QGIS plugin
 A plugin to help make Vision Zero Polygons
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                            -------------------
        begin                : 2023-05-27
        git sha              : $Format:%H$
        copyright            : (C) 2023 by DTS
        email                : frank.hereford@austintexas.gov
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
#import sys
#sys.path.insert(0, '/Users/frank/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/polygonizer/')

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal

#from qgis.core import (
    #QgsProject,
    #QgsVectorLayer
#)

from qgis.core import *
from qgis.utils import *

#from qgis.utils import (
    #iface
#)

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'polygonizer_dockwidget_base.ui'))


class PolygonizerDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(PolygonizerDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.printHelloWorld.clicked.connect(self.eventPushButtonDoSomethingOnClick)

    def eventPushButtonDoSomethingOnClick(self):
        project = QgsProject.instance()


        #layers = project.mapLayers()
        #print("Layers:")
        #print(layers)
        #for layer_key in layers:
            #layer = layers[layer_key]
            #print("Layer", layer.id(), "is a", layer.type())
        #print()

        # create layer
        vl = QgsVectorLayer("MultiLineString", "temporary_lines", "memory")
        crs = QgsCoordinateReferenceSystem("EPSG:2277")
        vl.setCrs(crs)
        pr = vl.dataProvider()
        vl.updateFields()

        active_layer = iface.activeLayer()
        selected_features = active_layer.selectedFeatures()
        for feature in selected_features:
            print("Feature ID:", type(feature))
            print("Feature ID:", feature.id())
            print("Feature attributes:", feature.attributes())
            print("Feature geometry:", feature.geometry())
            pr.addFeatures([feature])
            print()

        vl.updateExtents()

        print("fields:", len(pr.fields()))
        print("features:", pr.featureCount())
        e = vl.extent()
        print("extent:", e.xMinimum(), e.yMinimum(), e.xMaximum(), e.yMaximum())

        # iterate over features
        features = vl.getFeatures()
        for fet in features:
            print("F:", fet.id(), fet.attributes(), fet.geometry().asWkt())

        project.addMapLayer(vl)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

