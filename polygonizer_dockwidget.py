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

    def compute_subsections(self, total_length, goal_length):
        if goal_length >= total_length:
            return 1, total_length
        else:
            num_subsections = round(total_length / goal_length)
            actual_length = total_length / num_subsections
            return num_subsections, actual_length

    def eventPushButtonDoSomethingOnClick(self):
        project = QgsProject.instance()


        layers = project.mapLayers()
        #print("Layers:")
        for layer_key in layers:
            layer = layers[layer_key]
            if layer.id().startswith("Workspace_"):
                #print("Layer", layer.id(), "is a", layer.type())
                project.removeMapLayer(layer.id())
        #print()

        # create layer
        selected_features_layer = QgsVectorLayer("LineString", "Workspace: Selected Features", "memory")
        crs = QgsCoordinateReferenceSystem("EPSG:2277")
        selected_features_layer.setCrs(crs)
        selected_features_provider = selected_features_layer.dataProvider()

        active_layer = iface.activeLayer()
        selected_features = active_layer.selectedFeatures()
        for feature in selected_features:
            #print("Feature ID:", type(feature))
            #print("Feature ID:", feature.id())
            #print("Feature attributes:", feature.attributes())
            #print("Feature geometry:", feature.geometry().asWkt()) 
            selected_features_provider.addFeatures([feature])
            #print()

        selected_features_layer.updateExtents()

        intersection_layer = QgsVectorLayer('Point?crs=EPSG:2277', 'Workspace: Intersection Points', 'memory')
        intersection_provider = intersection_layer.dataProvider()

        # iterate over features, find intersecting features, so we can create a point at each intersection
        features = selected_features_layer.getFeatures()
        list_of_features = list(features)
        for i in range(len(list_of_features)):
            for j in range(i+1, len(list_of_features)):
                #print(f"Comparing {list_of_features[i].id()} and {list_of_features[j].id()}")
                intersection = list_of_features[i].geometry().intersection(list_of_features[j].geometry())
                #print("Intersection:", intersection)
                intersection_feature = QgsFeature()
                intersection_feature.setGeometry(intersection)
                intersection_provider.addFeature(intersection_feature)
        
        intersection_layer.updateExtents()
        
        # Delete duplicate features, so we have a single intersection point for each intersection
        index = QgsSpatialIndex()
        delete_ids = []
        for feature in intersection_layer.getFeatures():
            # If the feature's geometry is already in the index, then it's a duplicate
            if list(index.intersects(feature.geometry().boundingBox())):
                # Store the feature's ID in our list of features to delete
                delete_ids.append(feature.id())
            else:
                # If it's not in the index, add it now
                index.addFeature(feature)
        #print("Delete IDs:", delete_ids)

        with edit(intersection_layer):
            intersection_layer.deleteFeatures(delete_ids)


        segmented_roads_layer = QgsVectorLayer("LineString", "Workspace: Segments", "memory")
        crs = QgsCoordinateReferenceSystem("EPSG:2277")
        segmented_roads_layer.setCrs(crs)
        segmented_roads_provider = segmented_roads_layer.dataProvider()

        for intersection in intersection_layer.getFeatures():
            print("Intersection:", intersection.id())
            for road in selected_features_layer.getFeatures():
                if intersection.geometry().intersects(road.geometry()):
                    print(f"Intersection {intersection.id()} intersects road {road.id()} of length {road.geometry().length()} feet.")

                    subsections = self.compute_subsections(road.geometry().length(), 200) # second argument is goal length in feet
                    print("Subsections: (count, practical_length)", subsections)

                    for i in range(subsections[0]):
                        start_point = road.geometry().interpolate(i * subsections[1]).asPoint()
                        end_point = road.geometry().interpolate((i + 1) * subsections[1]).asPoint()
                        print("Start point:", start_point)
                        print("End point:", end_point)

                        start_distance = road.geometry().lineLocatePoint(QgsGeometry.fromPointXY(start_point))
                        end_distance = road.geometry().lineLocatePoint(QgsGeometry.fromPointXY(end_point))
                        print("Start distance:", start_distance)
                        print("End distance:", end_distance)

                        if start_distance > end_distance:
                            start_distance, end_distance = end_distance, start_distance

                        print("Type: ", type(road.geometry()))
                        multiline = road.geometry().asMultiPolyline()

                        # Flatten the list of lists to get a single list of points
                        points = [point for sublist in multiline for point in sublist]

                        # Create a LineString from these points
                        linestring = QgsLineString(points)

                        #linestring = QgsLineString(road.geometry().asPolyline())
                        segment = linestring.curveSubstring(start_distance, end_distance)

                        segment_feature = QgsFeature()
                        segment_feature.setGeometry(QgsGeometry.fromPolyline(segment))
                        
                        segmented_roads_provider.addFeatures([segment_feature])

                    #start_point = road.geometry().interpolate(i * subsections[1]).asPoint()
                    #end_point = road.geometry().interpolate((i + 1) * subsections[1]).asPoint()
                    #print("Start point:", start_point)
                    #print("End point:", end_point)
                    
                    #segment = QgsFeature()
                    #segment.setGeometry(QgsGeometry.fromPolylineXY([start_point, end_point]))
                    #segmented_roads_provider.addFeatures([segment])


                    #intersection["road_id"] = road.id()
                    #intersection_layer.updateFeature(intersection)
        
        intersection_layer.updateExtents()
        

        
        project.addMapLayer(selected_features_layer)
        project.addMapLayer(intersection_layer)
        project.addMapLayer(segmented_roads_layer)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

