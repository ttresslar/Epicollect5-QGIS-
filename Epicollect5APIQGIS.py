#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 25 05:14:27 2019

@author: ttresslar
"""
#import the relevant libraries
import requests
import urllib

#this is a function that gets the access token from the Epicollect5 API
def _getToken():
    headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
                }
    params = {
      "grant_type": "client_credentials",
      "client_id":  api_id	,
      "client_secret": api_secret
    }

    rqst = requests.post(url='https://five.epicollect.net/api/oauth/token',
                         headers=headers,
                         data=urllib.parse.urlencode(params)
                         )
    token = rqst.json()
    return token

#here we pull the first 50 entries from the website, along with a link for the next 
def _getEntries():
    token = _getToken()
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer {0}'.format(token)}
    axs = requests.get(
            url='https://five.epicollect.net/api/export/entries/' + api_slug,
            headers=headers
             )
    dta = axs.json()
    return dta


#this is a function that we will call for each successive entry, it takes the parameter "nxt" and turn
#it into the next page
def _getNextEntry(nxt):
    token = _getToken()
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer {0}'.format(token)}

    axs2 = requests.get(
                url=nxt['links']['next'],
                headers=headers
                )
    nxt = axs2.json()
    return nxt

#now the QGIS-y stuff, import the package we need
from qgis.PyQt.QtCore import QVariant
#and start the function
def _createGPSPoints():
    
    #here we create a list where we'll put our data, and call the function 
    #that gets the data for us (which then calls the function to get the token)
    _entries = []
    dta = _getEntries()
    #let's add the entries from each call to our  list
    _entries.append(dta['data']['entries'])
    
    #now we'll loop through the data until there are no more entries. 
    while dta['links']['next'] is not None:
        dta = _getNextEntry(dta)
        _entries.append(dta['data']['entries'])
    
    #now we'll create a flat list that we can 'unpack" the entries from each page
    flat_entries = []
    #and loop through to get rid of the sub lists
    for sublist in _entries:
        for item in sublist:
            flat_entries.append(item)
    
    #here we'll print out how many entries there are total...just so we know
    print("There are " + str(len(flat_entries)) + " entries")
    
    #then we'll pull the "keys" from the first entry so that we can make attribute headers
    hdrs = flat_entries[0].keys()
    
    #we'll create a temporary point layer and set the data for it
    vl = QgsVectorLayer("Point", "Epicollect5", "memory")
    pr = vl.dataProvider()
    #now we create our header labels
    for key in hdrs:
        pr.addAttributes([QgsField(key, QVariant.String)])
    #don't forget to update
    vl.updateFields()
    #now we'll loop through the entries to create points with attribute, I'm also creating 
    #a counter that we'll use later
    i=0
    for _entry in flat_entries:
        #we'll make a blank array that we can fill with attributes later
        attrbts = []
        for key, value in _entry.items():
            #if the value is a dictionary, that means we've found our GPS coordinates
            #let's separate them out and make sure they're not null
            if type(value) == dict and value['latitude'] != '':
                x = value['longitude']
                y = value['latitude']
                #we'll save the lat and lon to make the point, but add an attribute for accuracy
                attrbts.append('accuracy: ' + str(value['accuracy']))
                i = i+1
            else:
                #otherwise, we'll just add the attribute to our list
                attrbts.append(str(value))
        #then we'll piece everything together:
        # we'll create a feature, set the points and attributes, then add it to the data layer
        f = QgsFeature()
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x,y)))
        f.setAttributes(attrbts)
        pr.addFeature(f)
        #don't forget to update
        vl.updateExtents()
    #when everything is done, we add the map layer
    QgsProject.instance().addMapLayer(vl)
    #and let's see how many printed onto the map
    print("Created " + str(i) + " points for " + str(len(_entries)) + " entries")
    print(str(len(flat_entries) - i) + " entries did not have GPS Coordinates")

#here we enter our data, call our function and watch the waterfall magic happen.
api_id = "ENTER YOUR CLIENT ID HERE"
api_secret= "ENTER YOUR CLIENT SECRET HERE"
api_slug = "ENTER YOUR SLUG HERE"
_createGPSPoints()
