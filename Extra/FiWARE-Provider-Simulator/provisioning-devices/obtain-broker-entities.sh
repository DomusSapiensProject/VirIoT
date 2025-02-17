#
#Copyright Odin Solutions S.L. All Rights Reserved.
#
#SPDX-License-Identifier: Apache-2.0
#

curl -G -X GET \
    'http://localhost:1026/v2/entities/urn:ngsi-ld:Device:001' \
    -H 'fiware-service: demo1' \
    -H 'fiware-servicepath: /demo' | python -m json.tool;

curl -G -X GET \
    'http://localhost:1026/v2/entities/urn:ngsi-ld:Device:002' \
    -H 'fiware-service: demo2' \
    -H 'fiware-servicepath: /demo' | python -m json.tool;