import base64
import json
from api_keys import faceplus, google, amazon, kairos, azure

sources = {
    'google': 'googlevision',
    'kairos': 'kairos',
    'face': 'faceplusplus',
    'azure': 'azure',
    'amz': 'amazon'
}

class Emotions:
    def __init__(self, img_name='', source='', anger=0, contempt=0, disgust=0, fear=0, joy=0, neutral=0, sadness=0, surprise=0):
        self.img_name = img_name
        self.source = source
        # emotions
        self.anger = anger
        self.contempt = contempt
        self.disgust = disgust
        self.fear = fear
        self.joy = joy
        self.neutral = neutral
        self.sadness = sadness
        self.surprise = surprise
    
    def formatted_output(self):
        return (self.img_name, self.source, {
            'id': '{}_{}'.format(self.img_name, self.source),
            'img_name': self.img_name,
            'source': self.source,
            'anger': self.anger,
            'disgust': self.disgust,
            'fear': self.fear,
            'joy': self.joy,
            'neutral': self.neutral,
            'sadness': self.sadness,
            'surprise': self.surprise
        })

class FaceplusAPI:
    def __init__(self, image):
        self.image = open('img\\'+image, 'rb')
        self.url = 'https://api-us.faceplusplus.com/facepp/v3/detect'
        self.request_method = 'post'
        self.sleep = 2
        self.source = sources['face']

    def get_image(self):
        return self.image

    def request_data(self):
        data = {
            'api_key': faceplus['key'],
            'api_secret': faceplus['secret'],
            'image_file': self.image,
            'return_attributes': 'gender,age,eyestatus,emotion'
        }
        return data

    def headers(self):
        return {}

    def std_output(self, json_response, id):
        emotions = json_response['faces'][0]['attributes']['emotion']
        anger = emotions['anger']
        disgust = emotions['disgust']
        fear = emotions['fear']
        joy = emotions['happiness']
        neutral = emotions['neutral']
        sadness = emotions['sadness']
        surprise = emotions['surprise']

        return Emotions(img_name=id, source=self.source, anger=anger, disgust=disgust, fear=fear, joy=joy, neutral=neutral, sadness=sadness, surprise=surprise)
    
        

class KairosAPI:
    def __init__(self, image):
        self.image = open('img\\'+image, 'rb')
        self.url = 'https://api.kairos.com/v2/media?landmarks=1&timeout=50'
        self.request_method = 'post'
        self.sleep = 3
        self.source = sources['kairos']

    def get_image(self):
        return self.image

    def request_data(self):
        data = {
            'source': self.image,
        }
        return data

    def headers(self):
        return {
            'app_id': kairos['id'],
            'app_key': kairos['key']
        }
    
    def std_output(self, json_response, id):
        # check if person is detected
        people = json_response['frames'][0]['people']
        if len(people) == 0:
            return Emotions(img_name=id, source=self.source, anger=0, disgust=0, fear=0, joy=0, sadness=0, surprise=0)

        emotions = people[0]['emotions']
        anger = emotions['anger']
        joy = emotions['joy']
        disgust = emotions['disgust']
        fear = emotions['fear']
        sadness = emotions['sadness']
        surprise = emotions['surprise']

        return Emotions(img_name=id, source=self.source, anger=anger, disgust=disgust, fear=fear, joy=joy, sadness=sadness, surprise=surprise)

class GoogleAPI:
    def __init__(self, image):
        self.image = image
        self.url = 'https://vision.googleapis.com/v1/images:annotate?key=' + google['key']
        self.request_method = 'post'
        self.sleep = 1
        self.source = sources['google']

    def get_image(self):
        img = open('img\\' + self.image, 'rb')
        data = img.read()
        b64 = base64.b64encode(data)
        return b64.decode('utf-8')

    def request_data(self):
        data = {
            'requests': [
                {
                    'image': {
                        'content': self.get_image()
                    },
                    'features': {
                        'type': 'FACE_DETECTION',
                        'maxResults': 1
                    }
                }
            ]
        }
        # request has to be sent in json format
        return json.dumps(data)

    def headers(self):
        return {}

    def likelihood_to_value(self, likelihood):
        likelihoods = {
            'UNKNOWN': -1,
            'VERY_UNLIKELY': 0,
            'UNLIKELY': 25,
            'POSSIBLE': 50,
            'LIKELY': 75,
            'VERY_LIKELY': 100
        }
        return likelihoods[likelihood]

    def std_output(self, json_response, id):
        face_annotations = json_response['responses'][0]['faceAnnotations'][0]
        joy = self.likelihood_to_value(face_annotations['joyLikelihood'])
        sorrow = self.likelihood_to_value(face_annotations['sorrowLikelihood'])
        anger = self.likelihood_to_value(face_annotations['angerLikelihood'])
        surprise = self.likelihood_to_value(face_annotations['surpriseLikelihood'])
        return Emotions(img_name=id, source=self.source, anger=anger, joy=joy, sadness=sorrow, surprise=surprise)

class AzureAPI:
    def __init__(self, image):
        self.image = open('img\\'+image, 'rb')
        self.url = 'https://westus.api.cognitive.microsoft.com/emotion/v1.0/recognize'
        self.request_method = 'post'
        # limits are 30,000 transactions, 20 per minute
        self.sleep = 4
        self.source = sources['azure']

    def get_image(self):
        return self.image

    def request_data(self):
        return self.image

    def headers(self):
        return {
            'Ocp-Apim-Subscription-Key': azure['key'],
            'Content-Type': 'application/octet-stream'
        }
    
    def std_output(self, json_response, id):
        emotions = json_response[0]['scores']
        m = 100

        anger    = emotions['anger']*m
        contempt = emotions['contempt']*m
        disgust  = emotions['disgust']*m
        fear     = emotions['fear']*m
        joy      = emotions['happiness']*m
        neutral  = emotions['neutral']*m
        sadness  = emotions['sadness']*m
        surprise = emotions['surprise']*m

        return Emotions(img_name=id, source=self.source, anger=anger, contempt=contempt, disgust=disgust, fear=fear, joy=joy, neutral=neutral, sadness=sadness, surprise=surprise)

def AmazonAPI(json_response, id):
    emotions = json_response['FaceDetails'][0]['Emotions']
    amz_conversion = {
        'ANGRY': 'anger',
        'DISGUSTED': 'disgust',
        'HAPPY': 'joy',
        'SAD': 'sadness',
        'SURPRISED': 'surprise'
    }

    e = {}
    for emotion in (x for x in emotions if x['Type'] in list(amz_conversion.keys())):
        e[amz_conversion[emotion['Type']]] = emotion['Confidence']
    print('emotions formatted are', e)

    return Emotions(img_name=id, source='amazon', anger=e.get('anger', 0), disgust=e.get('disgust', 0), joy=e.get('joy', 0), sadness=e.get('sadness', 0), surprise=e.get('surprise', 0))