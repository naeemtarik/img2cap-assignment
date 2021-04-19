"""
COMP5623M Coursework on Image Caption Generation


python decoder.py


"""

import torch
import numpy as np

import torch.nn as nn
from torchvision import transforms
from torch.nn.utils.rnn import pack_padded_sequence
from PIL import Image

from datasets import Flickr8k_Images, Flickr8k_Features
from models import DecoderRNN, EncoderCNN
from utils import *
from config import *

# Extra Imports
from tqdm import tqdm

# if false, train model; otherwise try loading model from checkpoint and evaluate
EVAL = False

# reconstruct the captions and vocab, just as in extract_features.py
lines = read_lines(TOKEN_FILE_TRAIN)
image_ids, cleaned_captions = parse_lines(lines)
vocab = build_vocab(cleaned_captions)

# device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# initialize the models and set the learning parameters
decoder = DecoderRNN(EMBED_SIZE, HIDDEN_SIZE, len(vocab), NUM_LAYERS).to(device)

if not EVAL:

    # load the features saved from extract_features.py
    print(len(lines))
    features = torch.load('features.pt', map_location=device)
    print("Loaded features", features.shape)

    features = features.repeat_interleave(5, 0)
    print("Duplicated features", features.shape)

    dataset_train = Flickr8k_Features(
        image_ids=image_ids,
        captions=cleaned_captions,
        vocab=vocab,
        features=features,
    )

    train_loader = torch.utils.data.DataLoader(
        dataset_train,
        batch_size=64,  # change as needed
        shuffle=True,
        num_workers=0,  # may need to set to 0
        collate_fn=caption_collate_fn,  # explicitly overwrite the collate_fn
    )

    # loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(decoder.parameters(), lr=LR)

    print(len(image_ids))
    print(len(cleaned_captions))
    print(features.shape)

    #########################################################################
    #
    #        QUESTION 1.3 Training DecoderRNN
    #
    #########################################################################

    # TODO (Done) write training loop on decoder here

    for epoch in range(NUM_EPOCHS):
        description = f'Training Phase: Epoch {epoch + 1} '
        with tqdm(total=len(dataset_train), desc=description, unit=' img', leave=True) as pbar:
            for batch in train_loader:
                image_features, captions, lengths = batch

                # for each batch, prepare the targets using this torch.nn.utils.rnn function
                targets = pack_padded_sequence(captions, lengths, batch_first=True)[0]

                # Zero out the gradients for optimizer to avoid accumulation
                optimizer.zero_grad()

                # Models forward pass
                outputs = decoder(image_features, captions, lengths)

                # Calculate Loss
                loss = criterion(outputs, targets)

                # Backpropagation of loss
                loss.backward()

                # Weight Updates
                optimizer.step()

                # Update Visual Progress of tqdm
                pbar.set_postfix(**{'Train CE Loss (running)': loss.item()})
                pbar.update(image_features.shape[0])

    # save model checkpoint after training
    torch.save(decoder, "decoder.ckpt")
    print('Checkpoint Saved!')

# if we already trained, and EVAL == True, reload saved model
else:

    data_transform = transforms.Compose([
        transforms.Resize(224),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize((0.485, 0.456, 0.406),  # using ImageNet norms
                             (0.229, 0.224, 0.225))])

    test_lines = read_lines(TOKEN_FILE_TEST)
    test_image_ids, test_cleaned_captions = parse_lines(test_lines)

    # load models
    encoder = EncoderCNN().to(device)
    decoder = torch.load("decoder.ckpt").to(device)
    encoder.eval()
    decoder.eval()  # generate caption, eval mode to not influence batchnorm

#########################################################################
#
#        QUESTION 2.1 Generating predictions on test data
# 
#########################################################################


# TODO define decode_caption() function in utils.py
# predicted_caption = decode_caption(word_ids, vocab)


#########################################################################
#
#        QUESTION 2.2-3 Caption evaluation via text similarity 
# 
#########################################################################


# Feel free to add helper functions to utils.py as needed,
# documenting what they do in the code and in your report
