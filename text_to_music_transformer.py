# -*- coding: utf-8 -*-
"""Text_to_Music_Transformer.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/asigalov61/Text-to-Music-Transformer/blob/main/Text_to_Music_Transformer.ipynb

# Text-to-Music Transformer (ver. 1.0)

***

Powered by tegridy-tools: https://github.com/asigalov61/tegridy-tools

***

WARNING: This complete implementation is a functioning model of the Artificial Intelligence. Please excercise great humility, care, and respect. https://www.nscai.gov/

***

#### Project Los Angeles

#### Tegridy Code 2024

***

# (GPU CHECK)
"""

#@title NVIDIA GPU check
!nvidia-smi

"""# (SETUP ENVIRONMENT)"""

#@title Install dependencies
!git clone --depth 1 https://github.com/asigalov61/Text-to-Music-Transformer
!pip install huggingface_hub
!pip install einops
!pip install torch-summary
!apt install fluidsynth #Pip does not work for some reason. Only apt works

# Commented out IPython magic to ensure Python compatibility.
#@title Import modules

print('=' * 70)
print('Loading core Text-to-Music Transformer modules...')

import os
import copy
import pickle
import secrets
import statistics
from time import time
import tqdm

print('=' * 70)
print('Loading main Text-to-Music Transformer modules...')
import torch

# %cd /content/Text-to-Music-Transformer

import TMIDIX

from midi_to_colab_audio import midi_to_colab_audio

from x_transformer_1_23_2 import *

import random

# %cd /content/
print('=' * 70)
print('Loading aux Text-to-Music Transformer modules...')

import matplotlib.pyplot as plt

from torchsummary import summary
from sklearn import metrics

from IPython.display import Audio, display

from huggingface_hub import hf_hub_download

from google.colab import files

print('=' * 70)
print('Done!')
print('Enjoy! :)')
print('=' * 70)

"""# (LOAD MODEL)"""

#@title Load Quad Music Transformer Pre-Trained Model

#@markdown Model precision option

model_precision = "bfloat16" # @param ["bfloat16", "float16"]

#@markdown bfloat16 == Half precision/faster speed (if supported, otherwise the model will default to float16)

#@markdown float16 == Full precision/fast speed

plot_tokens_embeddings = True # @param {type:"boolean"}

print('=' * 70)
print('Loading Text-to-Music Transformer Pre-Trained Model...')
print('Please wait...')
print('=' * 70)

full_path_to_models_dir = "/content/Text-to-Music-Transformer/Model"

model_checkpoint_file_name = 'Text_to_Music_Transformer_Medium_Trained_Model_33934_steps_0.6093_loss_0.813_acc.pth'
model_path = full_path_to_models_dir+'/'+model_checkpoint_file_name

if os.path.isfile(model_path):
  print('Model already exists...')

else:
  hf_hub_download(repo_id='asigalov61/Text-to-Music-Transformer',
                  filename=model_checkpoint_file_name,
                  local_dir='/content/Text-to-Music-Transformer/Model/',
                  local_dir_use_symlinks=False)

print('=' * 70)
print('Instantiating model...')

device_type = 'cuda'

if model_precision == 'bfloat16' and torch.cuda.is_bf16_supported():
  dtype = 'bfloat16'
else:
  dtype = 'float16'

if model_precision == 'float16':
  dtype = 'float16'

ptdtype = {'bfloat16': torch.bfloat16, 'float16': torch.float16}[dtype]
ctx = torch.amp.autocast(device_type=device_type, dtype=ptdtype)

SEQ_LEN = 4096

# instantiate the model

model = TransformerWrapper(
    num_tokens = 2572,
    max_seq_len = SEQ_LEN,
    attn_layers = Decoder(dim = 2048, depth = 8, heads = 16, attn_flash = True)
)

model = AutoregressiveWrapper(model, ignore_index=2571)

model.cuda()
print('=' * 70)

print('Loading model checkpoint...')

model.load_state_dict(torch.load(model_path))
print('=' * 70)

model.eval()

print('Done!')
print('=' * 70)

print('Model will use', dtype, 'precision...')
print('=' * 70)

# Model stats
print('Model summary...')
summary(model)

# Plot Token Embeddings
if plot_tokens_embeddings:
  tok_emb = model.net.token_emb.emb.weight.detach().cpu().tolist()

  cos_sim = metrics.pairwise_distances(
    tok_emb, metric='cosine'
  )
  plt.figure(figsize=(7, 7))
  plt.imshow(cos_sim, cmap="inferno", interpolation="nearest")
  im_ratio = cos_sim.shape[0] / cos_sim.shape[1]
  plt.colorbar(fraction=0.046 * im_ratio, pad=0.04)
  plt.xlabel("Position")
  plt.ylabel("Position")
  plt.tight_layout()
  plt.plot()
  plt.savefig("/content/Text-to-Music-Transformer-Tokens-Embeddings-Plot.png", bbox_inches="tight")

"""# (SETUP MODEL CHANNELS MIDI PATCHES)"""

# @title Setup and load model channels MIDI patches

model_channel_0_piano_family = "Acoustic Grand" # @param ["Acoustic Grand", "Bright Acoustic", "Electric Grand", "Honky-Tonk", "Electric Piano 1", "Electric Piano 2", "Harpsichord", "Clav"]
model_channel_1_chromatic_percussion_family = "Music Box" # @param ["Celesta", "Glockenspiel", "Music Box", "Vibraphone", "Marimba", "Xylophone", "Tubular Bells", "Dulcimer"]
model_channel_2_organ_family = "Church Organ" # @param ["Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ", "Reed Organ", "Accordion", "Harmonica", "Tango Accordion"]
model_channel_3_guitar_family = "Acoustic Guitar(nylon)" # @param ["Acoustic Guitar(nylon)", "Acoustic Guitar(steel)", "Electric Guitar(jazz)", "Electric Guitar(clean)", "Electric Guitar(muted)", "Overdriven Guitar", "Distortion Guitar", "Guitar Harmonics"]
model_channel_4_bass_family = "Fretless Bass" # @param ["Acoustic Bass", "Electric Bass(finger)", "Electric Bass(pick)", "Fretless Bass", "Slap Bass 1", "Slap Bass 2", "Synth Bass 1", "Synth Bass 2"]
model_channel_5_strings_family = "Violin" # @param ["Violin", "Viola", "Cello", "Contrabass", "Tremolo Strings", "Pizzicato Strings", "Orchestral Harp", "Timpani"]
model_channel_6_ensemble_family = "Choir Aahs" # @param ["String Ensemble 1", "String Ensemble 2", "SynthStrings 1", "SynthStrings 2", "Choir Aahs", "Voice Oohs", "Synth Voice", "Orchestra Hit"]
model_channel_7_brass_family = "Trumpet" # @param ["Trumpet", "Trombone", "Tuba", "Muted Trumpet", "French Horn", "Brass Section", "SynthBrass 1", "SynthBrass 2"]
model_channel_8_reed_family = "Alto Sax" # @param ["Soprano Sax", "Alto Sax", "Tenor Sax", "Baritone Sax", "Oboe", "English Horn", "Bassoon", "Clarinet"]
model_channel_9_pipe_family = "Flute" # @param ["Piccolo", "Flute", "Recorder", "Pan Flute", "Blown Bottle", "Skakuhachi", "Whistle", "Ocarina"]
model_channel_10_synth_lead_family = "Lead 8 (bass+lead)" # @param ["Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)", "Lead 4 (chiff)", "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass+lead)"]
model_channel_11_synth_pad_family = "Pad 2 (warm)" # @param ["Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)", "Pad 4 (choir)", "Pad 5 (bowed)", "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)"]
model_channel_12_synth_effects_family = "FX 3 (crystal)" # @param ["FX 1 (rain)", "FX 2 (soundtrack)", "FX 3 (crystal)", "FX 4 (atmosphere)", "FX 5 (brightness)", "FX 6 (goblins)", "FX 7 (echoes)", "FX 8 (sci-fi)"]
model_channel_13_ethnic_family = "Banjo" # @param ["Sitar", "Banjo", "Shamisen", "Koto", "Kalimba", "Bagpipe", "Fiddle", "Shanai"]
model_channel_14_percussive_family = "Melodic Tom" # @param ["Tinkle Bell", "Agogo", "Steel Drums", "Woodblock", "Taiko Drum", "Melodic Tom", "Synth Drum", "Reverse Cymbal"]
model_channel_15_sound_effects_family = "Bird Tweet" # @param ["Guitar Fret Noise", "Breath Noise", "Seashore", "Bird Tweet", "Telephone Ring", "Helicopter", "Applause", "Gunshot"]
model_channel_16_drums_family = "Drums" # @param ["Drums"]

def txt2tokens(txt):
    return [ord(char)+2440 if 0 < ord(char) < 128 else 0+2440 for char in txt.lower()]

def tokens2txt(tokens):
    return [chr(tok-2440) for tok in tokens if 0+2440 < tok < 128+2440 ]


print('=' * 70)
print('Setting up patches...')
print('=' * 70)

instruments = [v[1] for v in TMIDIX.Number2patch.items()]

patches = [instruments.index(model_channel_0_piano_family),
                       instruments.index(model_channel_1_chromatic_percussion_family),
                       instruments.index(model_channel_2_organ_family),
                       instruments.index(model_channel_3_guitar_family),
                       instruments.index(model_channel_4_bass_family),
                       instruments.index(model_channel_5_strings_family),
                       instruments.index(model_channel_6_ensemble_family),
                       instruments.index(model_channel_7_brass_family),
                       instruments.index(model_channel_8_reed_family),
                       9, # Drums patch
                       instruments.index(model_channel_9_pipe_family),
                       instruments.index(model_channel_10_synth_lead_family),
                       instruments.index(model_channel_11_synth_pad_family),
                       instruments.index(model_channel_12_synth_effects_family),
                       instruments.index(model_channel_13_ethnic_family),
                       instruments.index(model_channel_15_sound_effects_family)
                       ]

print('Done!')
print('=' * 70)

"""# (TEXT-TO-MUSIC GENERATION)"""

#@title Standard Text-to-Music Generator

#@markdown Prompt settings

song_title_prompt = "Nothing Else Matters" # @param {type:"string"}
open_ended_prompt = False # @param {type:"boolean"}

#@markdown Generation settings

number_of_tokens_to_generate = 525 # @param {type:"slider", min:30, max:8190, step:3}
number_of_batches_to_generate = 4 #@param {type:"slider", min:1, max:16, step:1}
temperature = 0.9 # @param {type:"slider", min:0.1, max:1, step:0.05}

#@markdown Other settings

render_MIDI_to_audio = True # @param {type:"boolean"}

print('=' * 70)
print('Text-to-Music Model Generator')
print('=' * 70)

if song_title_prompt == '':
  outy = [2569]

else:
  if open_ended_prompt:
    outy = [2569] + txt2tokens(song_title_prompt)

  else:
    outy = [2569] + txt2tokens(song_title_prompt) + [2570]

print('Selected prompt sequence:')
print(outy[:12])
print('=' * 70)

torch.cuda.empty_cache()

inp = [outy] * number_of_batches_to_generate

inp = torch.LongTensor(inp).cuda()

with ctx:
  out = model.generate(inp,
                        number_of_tokens_to_generate,
                        temperature=temperature,
                        return_prime=True,
                        verbose=True)

out0 = out.tolist()

print('=' * 70)
print('Done!')
print('=' * 70)

torch.cuda.empty_cache()

#======================================================================

print('Rendering results...')

for i in range(number_of_batches_to_generate):

  print('=' * 70)
  print('Batch #', i)
  print('=' * 70)

  out1 = out0[i]

  print('Sample INTs', out1[:12])
  print('=' * 70)

  print('Generated song title:', ''.join(tokens2txt(out1)).title())
  print('=' * 70)

  if len(out1) != 0:

      song = out1
      song_f = []

      time = 0
      dur = 0
      vel = 90
      pitch = 0
      channel = 0

      for ss in song:

          if 0 <= ss < 128:

              time += ss * 32

          if 128 <= ss < 256:

              dur = (ss-128) * 32

          if 256 <= ss < 2432:

              chan = (ss-256) // 128

              if chan < 9:
                  channel = chan
              elif 9 < chan < 15:
                  channel = chan+1
              elif chan == 15:
                  channel = 15
              elif chan == 16:
                  channel = 9

              pitch = (ss-256) % 128

          if 2432 <= ss < 2440:

              vel = (((ss-2432)+1) * 15)-1

              song_f.append(['note', time, dur, channel, pitch, vel, chan*8 ])

      stats = TMIDIX.Tegridy_ms_SONG_to_MIDI_Converter(song_f,
                                                        output_signature = 'Text-to-Music Transformer',
                                                        output_file_name = '/content/Text-to-Music-Transformer-Composition_'+str(i),
                                                        track_name='Project Los Angeles',
                                                        list_of_MIDI_patches=patches
                                                        )


      print('=' * 70)
      print('Displaying resulting composition...')
      print('=' * 70)

      fname = '/content/Text-to-Music-Transformer-Composition_'+str(i)

      if render_MIDI_to_audio:
        midi_audio = midi_to_colab_audio(fname + '.mid')
        display(Audio(midi_audio, rate=16000, normalize=False))

      TMIDIX.plot_ms_SONG(song_f, plot_title=fname)

"""# Congrats! You did it! :)"""