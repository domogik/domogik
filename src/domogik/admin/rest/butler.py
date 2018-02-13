# -*- coding: utf-8 -*-

from domogik.admin.application import app, json_response, jsonp_response, timeit
import sys
import os
import domogik
import json
from subprocess import Popen, PIPE
from flask import request, abort, Response
from domogikmq.message import MQMessage
from domogikmq.reqrep.client import MQSyncReq
from domogik.common.utils import ucode
import traceback
from flask_login import login_required
import requests
import tempfile
from distutils.spawn import find_executable



@app.route('/rest/butler/discuss', methods=['GET'])
@jsonp_response
@login_required
@timeit
def api_butler_discuss_get():
    """
    @api {get} /butler/discuss Discuss with the butler with a GET request
    @apiName getButlerDiscuss
    @apiGroup Butler
    @apiVersion 0.5.0

    @apiParam data The json data for the butler
    @apiParam callback The callback name (automatically added by jquery)

    @apiExample Example usage with wget
        If authentication is activated, you will need to also use these options : --auth-no-challenge --http-user=admin --http-password=123 
        $ wget -qO- 'http://192.168.1.10:40406/rest/butler/discuss?callback=foo&data={"text" : "hello", "source" : "a_script"}' --header="Content-type: application/json"
        foo({
            "identity": "Aria", 
            "location": null, 
            "media": null, 
            "mood": null, 
            "reply_to": "a_script", 
            "sex": "female", 
            "text": "hi"
        })

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 
        foo({
            "identity": "Aria", 
            "location": null, 
            "media": null, 
            "mood": null, 
            "reply_to": "a_script", 
            "sex": "female", 
            "text": "hi"
        })

    @apiErrorExample Error while decoding the input data
        HTTTP/1.1 400 Bad Request
        foo({
            'error' : 'Error while decoding received json data. Error is : ...'
        })
    
    @apiErrorExample Butler did not respond in time
        HTTTP/1.1 500
        foo({
            'error': 'The butler did not respond'
        })
    
    @apiErrorExample Other error
        HTTTP/1.1 500 
        foo({
            'error': 'Error while parsing butler response : ...'
        })
    """
    try:
        json_data = json.loads(request.args['data'])
        if 'callback' in request.args:
            callback = request.args['callback']
        else:
            callback = "callback_not_defined"
    except:
        app.logger.error(u"Error while decoding received json data. Error is : {0}".format(traceback.format_exc()))
        return 400, {'error': u"Error while decoding received json data. Error is : {0}".format(traceback.format_exc())}, "None"

    cli = MQSyncReq(app.zmq_context)

    msg = MQMessage()
    msg.set_action('butler.discuss.do')
    msg.set_data(json_data)

    # do the request
    # we allow a long timeout because the butler can take some time to respond...
    # some functions are quite long (requests to external webservices, ...)
    resp = cli.request('butler', msg.get(), timeout=60)
    if resp:
        try:
            response = resp.get_data()
            return 200, response, callback
        except:
            app.logger.error(u"Error while parsing butler response : {0}".format(resp))
            return 500, {'error': u"Error while parsing butler response : {0}".format(resp) }, callback
    else:
        app.logger.error(u"The butler did not respond")
        return 500, {'error': "The butler did not respond"}, callback




@app.route('/rest/butler/discuss', methods=['POST'])
@json_response
@login_required
@timeit
def api_butler_discuss_post():
    """
    @api {post} /butler/discuss Discuss with the butler with a POST request
    @apiName postButlerDiscuss
    @apiGroup Butler
    @apiVersion 0.5.0


    @apiExample Example usage with wget
        If authentication is activated, you will need to also use these options : --auth-no-challenge --http-user=admin --http-password=123 
        $ wget -qO- http://192.168.1.10:40406/rest/butler/discuss --post-data='{"text" : "hello", "source" : "a_script"}' --header="Content-type: application/json"
        {
            "identity": "Aria", 
            "location": null, 
            "media": null, 
            "mood": null, 
            "reply_to": "a_script", 
            "sex": "female", 
            "text": "hi"
        }

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 
        {
            "identity": "Aria", 
            "location": null, 
            "media": null, 
            "mood": null, 
            "reply_to": "a_script", 
            "sex": "female", 
            "text": "hi"
        }

    @apiErrorExample Error while reading the input data
        HTTTP/1.1 400 Bad Request
        {
            'error' : 'Error while decoding received json data. Error is : ....'
        }
    
    @apiErrorExample Butler did not respond in time
        HTTTP/1.1 500 
        {
            'error' : 'The butler did not respond'
        }
    
    @apiErrorExample Other error
        HTTTP/1.1 500
        {
            'error' : 'Error while parsing butler response : ...'
        }
    """
    try:
        json_data = json.loads(request.data)
    except:
        msg = u"Error while decoding received json data. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return 400, {'error': msg}

    cli = MQSyncReq(app.zmq_context)

    msg = MQMessage()
    msg.set_action('butler.discuss.do')
    msg.set_data(json_data)

    # do the request
    # we allow a long timeout because the butler can take some time to respond...
    # some functions are quite long (requests to external webservices, ...)
    resp = cli.request('butler', msg.get(), timeout=60)
    if resp:
        try:
            response = resp.get_data()
            return 200, response
        except:
            msg = u"Error while parsing butler response : {0}".format(resp)
            app.logger.error(msg)
            return 500, {'error': msg}
    else:
        msg = u"The butler did not respond"
        app.logger.error(msg)
        return 500, {'error': msg}






@app.route('/rest/butler/audio_input_discuss', methods=['POST'])
@json_response
@login_required
@timeit
def api_butler_audio_input_discuss_post():
    """
    @api {post} /butler/audio_input_discuss Discuss with the butler by sending it directly an audio file. The response will be the text response in a json object
    @apiName postButlerDiscuss
    @apiGroup Butler
    @apiVersion 0.6.0

    @apiExample Example usage with curl
        # replace pico2wave with some microphone capture command
        pico2wave -l "en-US" -w /tmp/test.wav "what time is it"
        # call the API
        curl -XPOST 'https://192.168.1.10:40406/rest/butler/audio_input_discuss' \
           -u admin:123 \
           -k \
           -i -L \
           -H "Content-Type: audio/wav" \
           --data-binary "@/tmp/test.wav" \
           -o /tmp/response.txt
        # display the response
        cat /tmp/response.txt


    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 
        {"text" : "The response.", ...}

    @apiSuccessExample Success-Response but wit.ai didn't heard anything:
        HTTTP/1.1 200 
        {"text" : "I didn't hear you."}

    @apiErrorExample Bad request
        HTTTP/1.1 400 
        {"error": "Error while decoding received audio data. Error is : ..."}

    @apiErrorExample Error if wit.ai is not configured :
        HTTTP/1.1 500 
        {"error": "The wit.ai token is not configured. Please configure it first."}

    @apiErrorExample Error while calling wit.ai :
        HTTTP/1.1 500 
        {"error": "Error while calling wit.ai with token '....'. Error is : ......"}

    @apiErrorExample Error while calling wit.ai (2) :
        HTTTP/1.1 500 
        {"error": "wit.ai response is not ok! Status code = '....'. Full response = '.....'"}

    @apiErrorExample Error while processing wit.ai response : 
        HTTTP/1.1 500 
        {"error": "Error while processing wit.ai json response. Json = '....'. Error is : ...."}

    @apiErrorExample Error while calling wit.ai :
        HTTTP/1.1 500 
        {"error": "Error while calling wit.ai with token '....'. Error is : ......"}

    @apiErrorExample Error while parsing the butler response : 
        HTTTP/1.1 500 
        {"error": "Error while parsing butler response : '....'. Error is : ...."}

    @apiErrorExample Error : the butler didn't respond in time :
        HTTTP/1.1 500 
        {"error": "The butler did not respond"}

    @apiErrorExample Error while requesting the butler :
        HTTTP/1.1 500 
        {"error": "Error while requesting the butler. Error is : ...."
    """
    app.logger.debug(u"Audio requets received for the butler.")
    app.logger.debug(u"Getting audio data...")
    # Get audio input
    try:
        audio_input = request.data
    except:
        msg = u"Error while decoding received audio data. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return 400, {'error' : msg}
    app.logger.debug(u"...ok")

    app.logger.debug(u"Calling wit.ai...")
    try:
        # call wit.ai to get the text from the audio file
        wit_url = 'https://api.wit.ai/speech'
        wit_token = None
        with app.db.session_scope():
            wit_token = app.db.get_core_config(key='wit_token')
        if wit_token == None or wit_token == "":
            msg = u"The wit.ai token is not configured. Please configure it first."
            app.logger.warning(msg)
            return 500, {'error' : msg}
        headers = {'authorization': 'Bearer ' + wit_token,
                   'Content-Type': 'audio/wav'}
    
        resp = requests.post(wit_url,
                             headers = headers,
                             data = audio_input)
        app.logger.debug(u"...ok")
    except:
        msg = u"Error while calling wit.ai with token '{0}'. Error is : {1}".format(wit_token, traceback.format_exc())
        app.logger.error(msg)
        return 500, {'error' : msg}


    # process response
    if resp.status_code != 200:
        msg = u"wit.ai response is not ok! Status code = '{0}'. Full response = '{1}'".format(resp.status_code, resp.content)
        app.logger.error(msg)
        return 500, {'error' : msg}

    try:
        json_data = json.loads(resp.content)
        text = json_data['_text']
        app.logger.debug(u"The text returned from wit.ai is '{0}'".format(text))
    except:
        msg = ucode("Error while processing wit.ai json response. Json = '{0}'. Error is : {1}".format(resp.content, traceback.format_exc()))
        app.logger.error(msg)
        return 500, {'error' : msg}

    # In case wit.ai returns no text detected...
    if text == None:
        lang = app.lang.replace("_", "-")
        msg_no_response = {'en-US' : u"I didn't hear you.",
                           'fr-FR' : u"Je ne vous ai pas entendu."}
        if not lang in msg_no_response:
            lang = 'en-US'
        return 200, {"text" : msg_no_response[lang]}



    # call the butler
    try:
        req = {
                "identity": "Rest butler audio input interface",
                "location": None,
                "media": "voice",
                "mood": None,
                "source": "Rest butler audio input interface",
                "reply_to": "Rest butler audio input interface",
                "sex": "female",   
                "text": text
              }
    
        app.logger.debug(u"Requesting the butler over MQ req/rep...")
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        msg.set_action('butler.discuss.do')
        msg.set_data(req)
    
        # do the request
        # we allow a long timeout because the butler can take some time to respond...
        # some functions are quite long (requests to external webservices, ...)
        resp = cli.request('butler', msg.get(), timeout=60)
        app.logger.debug(u"...done")
        if resp:
            try:
                response = resp.get_data()
                app.logger.debug(u"Butler response : '{0}'".format(response))
                return 200, response
            except:
                msg = u"Error while parsing butler response : '{0}'. Error is : {1}".format(resp, traceback.format_exc())
                app.logger.error(msg)
                return 500, {'error' : msg}
        else:
            msg = u"The butler did not respond"
            app.logger.error(msg)
            return 500, {'error' : msg}
    except:
        msg = u"Error while requesting the butler. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return 500, {'error' : msg}



@app.route('/rest/butler/audio_discuss', methods=['POST'])
@login_required
@timeit
def api_butler_audio_discuss_post():
    """
    @api {post} /butler/audio_discuss Discuss with the butler by sending it directly an audio file. The response will be another audio file.
    @apiName postButlerDiscuss
    @apiGroup Butler
    @apiVersion 0.6.0


    @apiExample Example usage with curl
        # replace pico2wave with some microphone capture command
        pico2wave -l "en-US" -w /tmp/test.wav "what time is it"
        # call the API
        curl -XPOST 'https://192.168.1.10:40406/rest/butler/audio_discuss' \
           -u admin:123 \
           -k \
           -i -L \
           -H "Content-Type: audio/wav" \
           --data-binary "@/tmp/test.wav" \
           -o /tmp/response.wav
        # play the response
        aplay /tmp/response.wav


    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 
        An audio output in wav format

    @apiErrorExample The tool pico2wave is not installed
        HTTTP/1.1 500 
        {
            "error": "Internal server error"
        }
    
    @apiErrorExample Other error
        HTTTP/1.1 200 
        An audio output in wav format with the error description
    """
    app.logger.debug(u"Audio requets received for the butler.")

    # First, check if the tool pico2wave is available. 
    # If not, raise a technical error
    pico_cmd = find_executable("pico2wave")
    if pico_cmd == None:
        msg = u"Error : the 'pico2wave' tools is not installed on the Domogik server. You will not be able to use this url."
        app.logger.error(msg)
        abort(500)

    # Now that we are sure that pico2wave is installed, we will return only audio messages from now. So the enduser which use this url will directly get the errors in audio ;)
    lang = app.lang.replace("_", "-")
    err_lang = lang
    errors = {
               'en-US' : 
                 {
                   'ERR_INPUT' : u"Incorrect input data.",
                   'ERR_CFG' : u"The configuration is not done for wit.ai.",
                   'ERR_CALL_WIT' : u"Error while calling wit.ai service.",
                   'ERR_WIT_RESPONSE' : u"Error while processing wit.ai response.",
                   'ERR_WIT_EMPTY_RESPONSE' : u"I didn't hear you.",
                   'ERR_CALL_REST' : u"Error while calling the butler."
                 },
               'fr-FR' : 
                 {
                   'ERR_INPUT' : u"Les données en entrées sont incorrectes.",
                   'ERR_CFG' : u"La configuration de Domogik n'a pas été faite pour wit.ai.",
                   'ERR_CALL_WIT' : u"Erreur lors de l'appel au service wit.ai.",
                   'ERR_WIT_RESPONSE' : u"Erreur dans la réponde de wit.ai.",
                   'ERR_WIT_EMPTY_RESPONSE' : u"Je ne vous ai pas bien entendu.",
                   'ERR_CALL_REST' : u"Erreur lors de l'appel au majordome."
                 }
              }
    if not err_lang in errors:
        err_lang = 'en-US'
    app.logger.debug(u"The errors language will be '{0}'".format(err_lang))
    


    app.logger.debug(u"Getting audio data...")
    # Get audio input
    try:
        audio_input = request.data
    except:
        msg = u"Error while decoding received audio data. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        wavdata = generate_waw_data(pico_cmd, errors[err_lang]["ERR_INPUT"], err_lang)
        return Response(wavdata, mimetype='audio/wav')
    app.logger.debug(u"...ok")

    app.logger.debug(u"Calling wit.ai...")
    try:
        # call wit.ai to get the text from the audio file
        wit_url = 'https://api.wit.ai/speech'
        wit_token = None
        with app.db.session_scope():
            wit_token = app.db.get_core_config(key='wit_token')
        if wit_token == None or wit_token == "":
            msg = u"The wit.ai token is not configured. Please configure it first."
            app.logger.warning(msg)
            wavdata = generate_waw_data(pico_cmd, errors[err_lang]["ERR_CFG"], err_lang)
            return Response(wavdata, mimetype='audio/wav')
        headers = {'authorization': 'Bearer ' + wit_token,
                   'Content-Type': 'audio/wav'}
    
        resp = requests.post(wit_url,
                             headers = headers,
                             data = audio_input)
        app.logger.debug(u"...ok")
    except:
        msg = u"Error while calling wit.ai with token '{0}'. Error is : {1}".format(wit_token, traceback.format_exc())
        app.logger.error(msg)
        wavdata = generate_waw_data(pico_cmd, errors[err_lang]["ERR_CALL_WIT"], err_lang)
        return Response(wavdata, mimetype='audio/wav')


    # process response
    if resp.status_code != 200:
        msg = u"wit.ai response is not ok! Status code = '{0}'. Full response = '{1}'".format(resp.status_code, resp.content)
        app.logger.error(msg)
        wavdata = generate_waw_data(pico_cmd, errors[err_lang]["ERR_WIT_RESPONSE"], err_lang)
        return Response(wavdata, mimetype='audio/wav')

    try:
        json_data = json.loads(resp.content)
        text = json_data['_text']
        app.logger.debug(u"The text returned from wit.ai is '{0}'".format(text))
    except:
        msg = ucode("Error while processing wit.ai json response. Json = '{0}'. Error is : {1}".format(resp.content, traceback.format_exc()))
        app.logger.error(msg)
        wavdata = generate_waw_data(pico_cmd, errors[err_lang]["ERR_WIT_RESPONSE"], err_lang)
        return Response(wavdata, mimetype='audio/wav')

    # In case wit.ai returns no text detected...
    if text == None:
        wavdata = generate_waw_data(pico_cmd, errors[err_lang]["ERR_WIT_EMPTY_RESPONSE"], err_lang)
        return Response(wavdata, mimetype='audio/wav')


    # call the butler
    try:
        req = {
                "identity": "Rest butler audio interface",
                "location": None,
                "media": "voice",
                "mood": None,
                "source": "Rest butler audio interface",
                "reply_to": "Rest butler audio interface",
                "sex": "female",
                "text": text
              }
    
        app.logger.debug(u"Requesting the butler over MQ req/rep...")
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        msg.set_action('butler.discuss.do')
        msg.set_data(req)
    
        # do the request
        # we allow a long timeout because the butler can take some time to respond...
        # some functions are quite long (requests to external webservices, ...)
        resp = cli.request('butler', msg.get(), timeout=60)
        app.logger.debug(u"...done")
        if resp:
            try:
                response = resp.get_data()
                app.logger.debug(u"Butler response : '{0}'".format(response))
    
                wavdata = generate_waw_data(pico_cmd, response["text"], lang)
                return Response(wavdata, mimetype='audio/wav')
            except:
                msg = u"Error while parsing butler response : {0}. Error is : {1}".format(resp, traceback.format_exc())
                app.logger.error(msg)
                wavdata = generate_waw_data(pico_cmd, errors[err_lang]["ERR_CALL_REST"], err_lang)
                return Response(wavdata, mimetype='audio/wav')
        else:
            msg = u"The butler did not respond"
            app.logger.error(msg)
            wavdata = generate_waw_data(pico_cmd, errors[err_lang]["ERR_CALL_REST"], err_lang)
            return Response(wavdata, mimetype='audio/wav')
    except:
        msg = u"Error while requesting the butler. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        wavdata = generate_waw_data(pico_cmd, errors[err_lang]["ERR_CALL_REST"], err_lang)
        return Response(wavdata, mimetype='audio/wav')









@app.route('/rest/tts/<string:text>', methods=['GET'])
@login_required
@timeit
def api_tts(text):
    """
    @api {get} /tts/ Send some text and get the corresponding speech in wav format in response.
    @apiName tts
    @apiGroup Butler
    @apiVersion 0.6.0


    @apiExample Example usage with curl
        # Call the url
        /usr/bin/curl  "https://192.168.1.10:40406/rest/tts/hello%10world" \
           -u admin:123 \
           -k \
           -H "Content-Type: text/text" \
           -o /tmp/tts.wav
        # Play the returned audio data
        aplay /tmp/tts.wav


    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 
        An audio output in wav format

    @apiErrorExample The tool pico2wave is not installed
        HTTTP/1.1 500 
        {
            "error": "Internal server error"
        }
    
    @apiErrorExample Other error
        HTTTP/1.1 200 
        An audio output in wav format with the error description
    """
    app.logger.debug(u"TTS requets received.")

    # First, check if the tool pico2wave is available. 
    # If not, raise a technical error
    pico_cmd = find_executable("pico2wave")
    if pico_cmd == None:
        msg = u"Error : the 'pico2wave' tools is not installed on the Domogik server. You will not be able to use this url."
        app.logger.error(msg)
        abort(500)

    # Now that we are sure that pico2wave is installed, we will return only audio messages from now. So the enduser which use this url will directly get the errors in audio ;)
    lang = app.lang.replace("_", "-")
    err_lang = lang
    errors = {
               'en-US' : 
                 {
                   'ERROR' : u"An error occured while generating the voice from the text.",
                 },
               'fr-FR' : 
                 {
                   'ERROR' : u"Une erreur est survenue lors de la conversion du texte en voix.",
                 }
              }
    if not err_lang in errors:
        err_lang = 'en-US'
    app.logger.debug(u"The errors language will be '{0}'".format(err_lang))
    

    try:
        wavdata = generate_waw_data(pico_cmd, text, lang)
        return Response(wavdata, mimetype='audio/wav')
    except:
        msg = u"Error while requesting the butler. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        wavdata = generate_waw_data(pico_cmd, errors[err_lang]["ERROR"], err_lang)
        return Response(wavdata, mimetype='audio/wav')








def generate_waw_data(pico_cmd, text, lang):
    wavfile = tempfile.NamedTemporaryFile(suffix = '.wav')
    wavfile_sox = tempfile.NamedTemporaryFile(suffix = '.wav')
    wavdata = None
    try:
        # we add a '. ' before to make the spoken text clearer on start... Without, on some short sentences, it is not very clean
        text = u". {0} .".format(text)

        cmd = u'{0} -l {1} -w {2} "{3}"'.format(pico_cmd, lang, wavfile.name, text)
        app.logger.debug(u"Executing command : '{0}'".format(cmd))
        pico_run = Popen(cmd, shell=True, 
                         stdout=PIPE, 
                         stderr=PIPE)
        out, err = pico_run.communicate()
        app.logger.debug(u"Pico stdout : {0}".format(out))
        app.logger.debug(u"Pico stderr : {0}".format(err))

        # Now, as the voice generated by pico2wave is not enough loud, we increase the generated wav file volume with sox.
        # In case sox is not installed/available, we skip this part silently
        sox_cmd = find_executable("sox")
        if sox_cmd is not None:
            cmd2 = "{0} -v 1.5 {1} {2}".format(sox_cmd, wavfile.name, wavfile_sox.name)
            app.logger.debug(u"Executing command : '{0}'".format(cmd2))
            sox_run = Popen(cmd2, shell=True, 
                            stdout=PIPE, 
                            stderr=PIPE)
            out, err = sox_run.communicate()
            app.logger.debug(u"Sox stdout : {0}".format(out))
            app.logger.debug(u"Sox stderr : {0}".format(err))

            # read the wav file
            wavfile_sox.seek(0)
            wavdata = wavfile_sox.read()
        else:
            app.logger.warning(u"The 'sox' utility is not found on the system : we will not increase the wav file volume")

            # read the wav file
            wavfile.seek(0)
            wavdata = wavfile.read()
    except:
        msg = u"Error while generating wave output with pico2wave... Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return None
    finally: 
        wavfile.close()
        wavfile_sox.close()
    return wavdata
