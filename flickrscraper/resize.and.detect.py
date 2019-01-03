#!/usr/bin/env python

from __future__ import print_function
# Copyright 2015 Google, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Change the target directory below to point to the dir containing photos
# Files will be resized to less than 4MB for Google Vision and analyzed for presence of faces. Non-face images are deleted.
# Needs google auth .json file env var


import os
import base64

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from PIL import Image
from PIL import ImageDraw
import glob
import PIL

target = "/path/to/target/folder/"


# [START get_vision_service]
def get_vision_service():
    credentials = GoogleCredentials.get_application_default()
    return discovery.build('vision', 'v1', credentials=credentials)
# [END get_vision_service]


def detect_face(face_file, max_results=4):
    """Uses the Vision API to detect faces in the given file.

    Args:
        face_file: A file-like object containing an image with faces.

    Returns:
        An array of dicts with information about the faces in the picture.
    """
    image_content = face_file.read()
    batch_request = [{
        'image': {
            'content': base64.b64encode(image_content).decode('utf-8')
        },
        'features': [{
            'type': 'FACE_DETECTION',
            'maxResults': max_results,
        }]
    }]

    service = get_vision_service()
    request = service.images().annotate(body={
        'requests': batch_request,
    })
    response = request.execute()

    return response['responses'][0]['faceAnnotations']


def highlight_faces(image, faces, output_filename):
    """Draws a polygon around the faces, then saves to output_filename.

    Args:
      image: a file containing the image with the faces.
      faces: a list of faces found in the file. This should be in the format
          returned by the Vision API.
      output_filename: the name of the image file to be created, where the
          faces have polygons drawn around them.
    """
    im = Image.open(image)
    draw = ImageDraw.Draw(im)  # noqa

    for face in faces:
        box = [(v.get('x', 0.0), v.get('y', 0.0))  # noqa
        for v in face['fdBoundingPoly']['vertices']]
        # draw.line(box + [box[0]], width=5, fill='#00ff00')
# removed the boxes, maybe they're useful later - josh
    # im.save(output_filename)


def main(input_filename, output_filename, max_results):
    with open(input_filename, 'rb') as image:
        faces = detect_face(image, max_results)
        print('Found {} face{}'.format(
            len(faces), '' if len(faces) == 1 else 's'))

        print('Writing to file {}'.format(output_filename))
        # Reset the file pointer, so we can read the file again
        image.seek(0)
        # highlight_faces(image, faces, output_filename)


if __name__ == '__main__':
    os.chdir(target)
    for file in glob.glob("*.jpg"):
        statinfo = os.stat(file)
        filesize = statinfo.st_size
        if filesize > 8000000:
            basewidth = 6000
            print(statinfo.st_size)
            print(file)
            img = Image.open(file)
            wpercent = (basewidth / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(wpercent)))
            img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
            img.save(file)
        if filesize > 4000000:
            basewidth = 4000
            print(statinfo.st_size)
            print(file)
            img = Image.open(file)
            wpercent = (basewidth / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(wpercent)))
            img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
            img.save(file)
        output = file
        max_results = '4'
        try:
            main(file, output, max_results)
        except:  # noqa
            os.remove(file)
