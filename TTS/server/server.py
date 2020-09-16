#!flask/bin/python
import argparse
import os

from flask import Flask, request, render_template, send_file
from TTS.server.synthesizer import Synthesizer
from TTS.utils.io import load_config


def create_argparser():
    def convert_boolean(x):
        return x.lower() in ['true', '1', 'yes']

    parser = argparse.ArgumentParser()
    parser.add_argument('--tts_checkpoint', type=str, help='path to TTS checkpoint file')
    parser.add_argument('--tts_config', type=str, help='path to TTS config.json file')
    parser.add_argument('--tts_speakers', type=str, help='path to JSON file containing speaker ids, if speaker ids are used in the model')
    parser.add_argument('--speaker_fileid', type=str, help="if tts_speakers is defined, name of speaker embedding reference file present in speakers.json, else target speaker_fileid if the model is multi-speaker.", default=None)
    parser.add_argument('--wavernn_lib_path', type=str, default=None, help='path to WaveRNN project folder to be imported. If this is not passed, model uses Griffin-Lim for synthesis.')
    parser.add_argument('--wavernn_checkpoint', type=str, default=None, help='path to WaveRNN checkpoint file.')
    parser.add_argument('--wavernn_config', type=str, default=None, help='path to WaveRNN config file.')
    parser.add_argument('--is_wavernn_batched', type=convert_boolean, default=False, help='true to use batched WaveRNN.')
    parser.add_argument('--vocoder_config', type=str, default=None, help='path to TTS.vocoder config file.')
    parser.add_argument('--vocoder_checkpoint', type=str, default=None, help='path to TTS.vocoder checkpoint file.')
    parser.add_argument('--port', type=int, default=5002, help='port to listen on.')
    parser.add_argument('--lang', type=str, default='en', help='language code for tokenizer')
    parser.add_argument('--use_cuda', type=convert_boolean, default=False, help='true to use CUDA.')
    parser.add_argument('--debug', type=convert_boolean, default=False, help='true to enable Flask debug mode.')
    parser.add_argument('--config_file', type=str, default=None, help='path to server config file')
    parser.add_argument('--use_cache', type=convert_boolean, default=False, help='true to use cache.')
    parser.add_argument('--cache_path', type=str, default=None, help='path where cached audio files are stored')
    return parser


synthesizer = None

embedded_models_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'model')

embedded_tts_folder = os.path.join(embedded_models_folder, 'tts')
tts_checkpoint_file = os.path.join(embedded_tts_folder, 'checkpoint.pth.tar')
tts_config_file = os.path.join(embedded_tts_folder, 'config.json')

embedded_vocoder_folder = os.path.join(embedded_models_folder, 'vocoder')
vocoder_checkpoint_file = os.path.join(embedded_vocoder_folder, 'checkpoint.pth.tar')
vocoder_config_file = os.path.join(embedded_vocoder_folder, 'config.json')

# These models are soon to be deprecated
embedded_wavernn_folder = os.path.join(embedded_models_folder, 'wavernn')
wavernn_checkpoint_file = os.path.join(embedded_wavernn_folder, 'checkpoint.pth.tar')
wavernn_config_file = os.path.join(embedded_wavernn_folder, 'config.json')

args = create_argparser().parse_args()

# load config file if specified, additional CLI args overwrite the ones from config file
if args.config_file is not None and os.path.isfile(args.config_file):
    print("loading config file:", args.config_file)
    args = load_config(args.config_file)   

# If these were not specified in the CLI args, use default values with embedded model files
if not args.tts_checkpoint and os.path.isfile(tts_checkpoint_file):
    args.tts_checkpoint = tts_checkpoint_file
if not args.tts_config and os.path.isfile(tts_config_file):
    args.tts_config = tts_config_file

if not args.vocoder_checkpoint and os.path.isfile(vocoder_checkpoint_file):
    args.vocoder_checkpoint = vocoder_checkpoint_file
if not args.vocoder_config and os.path.isfile(vocoder_config_file):
    args.vocoder_config = vocoder_config_file

if not args.wavernn_checkpoint and os.path.isfile(wavernn_checkpoint_file):
    args.wavernn_checkpoint = wavernn_checkpoint_file
if not args.wavernn_config and os.path.isfile(wavernn_config_file):
    args.wavernn_config = wavernn_config_file

# when cache is used -:create cache path if missing
if args.use_cache and args.cache_path is not None:
    if not os.path.isdir(args.cache_path):
        os.makedirs(args.cache_path)

synthesizer = Synthesizer(args)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/tts', methods=['GET'])
def tts():
    text = request.args.get('text')
    print(" > Model input: {}".format(text))
    data = synthesizer.tts(text)
    return send_file(data, mimetype='audio/wav', attachment_filename='output.wav', )


def main():
    app.run(debug=args.debug, host='0.0.0.0', port=args.port)


if __name__ == '__main__':
    main()
