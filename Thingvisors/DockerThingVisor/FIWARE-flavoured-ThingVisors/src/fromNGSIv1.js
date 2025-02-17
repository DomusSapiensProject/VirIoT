/*

Copyright Odin Solutions S.L. All Rights Reserved.

SPDX-License-Identifier: Apache-2.0

*/

"use strict";

var libWrapperUtils = require("./wrapperUtils");

//body --> Only One Orion Context Entity (NGSI v1) --> An element of contextResponses Array
//return --> Only One Orion Context Entity (NGSI-LD)
function fromNGSIv1toNGSILD(body,ldContext){

  /*
  var bodyContextResponses = body.contextResponses
  var bodyContextResponsesLength = bodyContextResponses.length
 
  var contextElement
  var entities={};
  var attributes
  */
  
  var contextElement = body.contextElement

  var entities={};
  var attributes={};
  var ocbType="", ocbId=""
  var matchKeyResponse=[]

/*
  for(var j=0; j< bodyContextResponsesLength;j++){
    contextElement = bodyContextResponses[j].contextElement;

    ocbType="", ocbId=""

    attributes = {};

    for(let ceAttr in contextElement){

      if (ceAttr == "attributes"){

        matchKeyResponse=[]

        for(var k=0; k< contextElement[ceAttr].length; k++) {

          matchKeyResponse =  match_keyNGSIv1(contextElement[ceAttr][k].name, contextElement[ceAttr][k], "", "", "")

          if (matchKeyResponse.length=2) {
            attributes[matchKeyResponse[0]] =  matchKeyResponse[1]
          }
        }

      } else if (ceAttr == "id"){
        attributes[ceAttr] = contextElement[ceAttr];
        ocbId = contextElement[ceAttr]
      } else if (ceAttr == "type") {//type
        attributes[ceAttr] = contextElement[ceAttr];
        ocbType = contextElement[ceAttr]
      }
    }

    attributes["id"] = format_uri(ocbType,ocbId)
    entities[attributes["id"]] = attributes
  }
*/

  for(let ceAttr in contextElement){

    if (ceAttr == "attributes"){

      matchKeyResponse=[]

      for(var k=0; k< contextElement[ceAttr].length; k++) {

        matchKeyResponse =  match_keyNGSIv1(contextElement[ceAttr][k].name, contextElement[ceAttr][k], "", "", "")

        if (matchKeyResponse.length=2) {
          attributes[matchKeyResponse[0]] =  matchKeyResponse[1]
        }
      }

    } else if (ceAttr == "id"){
      attributes[ceAttr] = contextElement[ceAttr];
      ocbId = contextElement[ceAttr]
    } else if (ceAttr == "type") {//type
      attributes[ceAttr] = contextElement[ceAttr];
      ocbType = contextElement[ceAttr]
    }
  }

  attributes["id"] = libWrapperUtils.format_uri(ocbType,ocbId)

  return attributes

}  


function match_keyNGSIv1(key, attribute, paramIn, paramOut, ldReversedContext) {
  var attrObject

  if (key.toUpperCase() == "dateCreated".toUpperCase() ) {
    return ["createdAt", attribute.value]
  } else if (key.toUpperCase() == "dateModified".toUpperCase() ) {
    return ["modifiedAt", attribute.value]
  } else if (key.toUpperCase() == "@context".toUpperCase() ) {
    return ["@context", attribute.value]
  //NGSI-LD Datetime format "observedAt"
  //Response: Error: "title": "Attribute must be a JSON object",
  } else if (key.toUpperCase() == "timestamp".toUpperCase() ) {
    //return ["observedAt", attribute.value]
    //return ["observedAt", {type: 'Property', value: attribute.value} ]
    return ["observedAt", {type: 'Property', value: {"@type": attribute.type, "@value": attribute.value}} ]
  } else {

    if (libWrapperUtils.AnyProp(key)) {

      attrObject={}

      const declType = attribute.type || attribute.Property || ""
      var isRelationship = false

      //Testing if the attribute will be a NGSI-LD relationship.
      if (!libWrapperUtils.ReferenceAttr(key) && declType != "Relationship" && declType != "Reference") { //No NGSI-LD relationship.
/*      
        if (declType.toUpperCase() == "geo:json".toUpperCase() ||        // { type:, value: {type: , coordinates:} }
            declType.toUpperCase() == "geo:point".toUpperCase() ||       // { type:, value: }
            declType.toUpperCase() == "geo:line".toUpperCase() ||        // { type:, value: }
            declType.toUpperCase() == "geo:box".toUpperCase() ||         // { type:, value: }
            declType.toUpperCase() == "geo:polygon".toUpperCase() ||     // { type:, value: }
            declType.toUpperCase() == "coords".toUpperCase() ||          // { type:, value: }
            declType.toUpperCase() == "Point".toUpperCase() ||           // {type: , coordinates:}
            declType.toUpperCase() == "LineString".toUpperCase() ||      // {type: , coordinates:}
            declType.toUpperCase() == "Polygon".toUpperCase() ||         // {type: , coordinates:}
            declType.toUpperCase() == "MultiPoint".toUpperCase() ||      // {type: , coordinates:}
            declType.toUpperCase() == "MultiLineString".toUpperCase() || // {type: , coordinates:}
            declType.toUpperCase() == "MultiPolygon".toUpperCase() ||    // {type: , coordinates:}
            key == "location") {
*/
        //Version 0: Only consider NGSI-v2 geo:json type attribute as a NGSI-LD GeoProperty.
        //Version 1: consider NGSI-v2 coords type attribute as a NGSI-LD GeoProperty geo:json point type.
        //Version 2: consider NGSI-v2 geo:point type attribute as a NGSI-LD GeoProperty geo:json point type.
        if (declType == "geo:json" || declType == "coords" || declType == "geo:point" || declType == "geo:polygon") {
          attrObject["type"] = "GeoProperty";
        } else {
          attrObject["type"] = "Property";
        }

        var valueType = ""

        if (declType.toUpperCase() == "DateTime".toUpperCase()) {
          valueType = "DateTime"
        }

        var valueAttr = attribute.value

        if (typeof valueAttr == "undefined") {
          valueAttr = attribute
        }

        //Version 1: consider NGSI-v2 coords type attribute as a NGSI-LD GeoProperty geo:json point type.
        //Version 2: consider NGSI-v2 geo:point type attribute as a NGSI-LD GeoProperty geo:json point type.
        if (declType == "coords" || declType == "geo:point") {
          valueAttr = {type: "Point", 
                      coordinates:[ parseFloat(attribute.value.split(",")[1]), parseFloat(attribute.value.split(",")[0]) ]
                      }
        } else if (declType == "geo:polygon") {
          
          var aux = []
          
          for(var i=0; i< attribute.value.length; i++){

            aux.push([ parseFloat(attribute.value[i].split(",")[1]), parseFloat(attribute.value[i].split(",")[0]) ])
          }

          valueAttr = {type: "Polygon", 
                      coordinates:[ aux ]
                      }
          
        }

        attrObject["value"] = libWrapperUtils.format_value(attrObject["type"], valueAttr, "",  valueType)

      } else { //No NGSI-LD relationship.
          isRelationship = true
          attrObject["type"] = "Relationship";
          attrObject["object"] = "";

          attrObject.object = libWrapperUtils.format_value(attrObject["type"], attribute.value, "",  "")
      }
      
      if (typeof attribute.metadatas != "undefined") {
        var metadataBody = attribute.metadatas

        for(var i=0; i< metadataBody.length; i++){
          if (metadataBody[i].name.toUpperCase()=="timestamp".toUpperCase()) {
            //TODO: Review --> I think it may do.
            //TODO: Review --> NGSI-LD DateTime format?.
            //attrObject["observedAt"] = metadataBody[i].value.split(".")[0]
            attrObject["observedAt"] = metadataBody[i].value
          } else if (metadataBody[i].name.toUpperCase()=="unitCode".toUpperCase()) {
            attrObject[metadataBody[i].name] = metadataBody[i].value
          } else if (metadataBody[i].name.toUpperCase()=="entityType".toUpperCase()) {

            if (isRelationship && typeof metadataBody[i].value != "undefined") {
              attrObject.object = libWrapperUtils.format_uri(metadataBody[i].value, attribute.value)
            }
          } else { 
            //attrObject[metadataBody[i].name] = match_keyNGSIv1(metadataBody[i].name, metadataBody[i], "", "")

            var matchKeyResponse = []

            matchKeyResponse = match_keyNGSIv1(metadataBody[i].name, metadataBody[i], "", "","")

            if (matchKeyResponse.length==2) {
              attrObject[metadataBody[i].name] = matchKeyResponse[1]
            }
          }
        }
      }
      return [key, attrObject]

    } else {
      return []
    }
  }
}

module.exports.fromNGSIv1toNGSILD = fromNGSIv1toNGSILD; 