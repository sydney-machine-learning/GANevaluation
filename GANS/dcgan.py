# -*- coding: utf-8 -*-
"""cGAN.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/122-ffDeYrEO587jj4OSkSUgI78EnvapD
"""

# Tensorflow / Keras
from tensorflow import keras                    # for building Neural Networks
from keras.models import Model, load_model      # for assembling a neural network model
from keras.layers import Input, Dense, Embedding, Reshape, Concatenate, Flatten, Dropout  # for adding layers
from keras.layers import Conv2D, Conv2DTranspose, MaxPool2D, ReLU, LeakyReLU  # for adding layers
from tensorflow.keras.utils import plot_model   # for plotting model diagram
from tensorflow.keras.optimizers import Adam    # for model optimization

# Data Manipulation
import numpy as np   # for data manipulation

# Visualization
import matplotlib.pyplot as plt # for data visualization

# Other utilities
import sys
import os

# Assign main directory to a variable
main_dir = os.path.dirname(sys.path[0])

def generator(latent_dim, in_shape=(7,7,1), n_cats=10):

    # Label Inputs
    in_label = Input(shape=(1,), name='Generator-Label-Input-Layer') # Input Layer
    lbls = Embedding(n_cats, 50, name='Generator-Label-Embedding-Layer')(in_label) # Embed label to vector

    # Scale up to image dimensions
    n_nodes = in_shape[0] * in_shape[1]
    lbls = Dense(n_nodes, name='Generator-Label-Dense-Layer')(lbls)
    lbls = Reshape((in_shape[0], in_shape[1], 1), name='Generator-Label-Reshape-Layer')(lbls) # New shape

    # Generator Inputs (latent vector)
    in_latent = Input(shape=latent_dim, name='Generator-Latent-Input-Layer')

    # Image Foundation
    n_nodes = 7 * 7 * 128 # number of nodes in the initial layer
    g = Dense(n_nodes, name='Generator-Foundation-Layer')(in_latent)
    g = ReLU(name='Generator-Foundation-Layer-Activation-1')(g)
    g = Reshape((in_shape[0], in_shape[1], 128), name='Generator-Foundation-Layer-Reshape-1')(g)

    # Combine both inputs so it has two channels
    concat = Concatenate(name='Generator-Combine-Layer')([g, lbls])

    # Hidden Layer 1
    g = Conv2DTranspose(filters=128, kernel_size=(4,4), strides=(2,2), padding='same', name='Generator-Hidden-Layer-1')(concat)
    g = ReLU(name='Generator-Hidden-Layer-Activation-1')(g)

    # Hidden Layer 2
    g = Conv2DTranspose(filters=128, kernel_size=(4,4), strides=(2,2), padding='same', name='Generator-Hidden-Layer-2')(g)
    g = ReLU(name='Generator-Hidden-Layer-Activation-2')(g)

    # Output Layer (Note, we use only one filter because we have a greysclae image. Color image would have three
    output_layer = Conv2D(filters=1, kernel_size=(7,7), activation='tanh', padding='same', name='Generator-Output-Layer')(g)

    # Define model
    model = Model([in_latent, in_label], output_layer, name='Generator')
    return model

def discriminator(in_shape=(28,28,1), n_cats=10):

    # Label Inputs
    in_label = Input(shape=(1,), name='Discriminator-Label-Input-Layer') # Input Layer
    lbls = Embedding(n_cats, 50, name='Discriminator-Label-Embedding-Layer')(in_label) # Embed label to vector

    # Scale up to image dimensions
    n_nodes = in_shape[0] * in_shape[1]
    lbls = Dense(n_nodes, name='Discriminator-Label-Dense-Layer')(lbls)
    lbls = Reshape((in_shape[0], in_shape[1], 1), name='Discriminator-Label-Reshape-Layer')(lbls) # New shape

    # Image Inputs
    in_image = Input(shape=in_shape, name='Discriminator-Image-Input-Layer')

    # Combine both inputs so it has two channels
    concat = Concatenate(name='Discriminator-Combine-Layer')([in_image, lbls])

    # Hidden Layer 1
    h = Conv2D(filters=64, kernel_size=(3,3), strides=(2,2), padding='same', name='Discriminator-Hidden-Layer-1')(concat)
    h = LeakyReLU(alpha=0.2, name='Discriminator-Hidden-Layer-Activation-1')(h)

    # Hidden Layer 2
    h = Conv2D(filters=128, kernel_size=(3,3), strides=(2,2), padding='same', name='Discriminator-Hidden-Layer-2')(h)
    h = LeakyReLU(alpha=0.2, name='Discriminator-Hidden-Layer-Activation-2')(h)
    h = MaxPool2D(pool_size=(3,3), strides=(2,2), padding='valid', name='Discriminator-MaxPool-Layer-2')(h) # Max Pool

    # Flatten and Output Layers
    h = Flatten(name='Discriminator-Flatten-Layer')(h) # Flatten the shape
    h = Dropout(0.2, name='Discriminator-Flatten-Layer-Dropout')(h) # Randomly drop some connections for better generalization

    output_layer = Dense(1, activation='sigmoid', name='Discriminator-Output-Layer')(h) # Output Layer

    # Define model
    model = Model([in_image, in_label], output_layer, name='Discriminator')

    # Compile the model
    model.compile(loss='binary_crossentropy', optimizer=Adam(learning_rate=0.0002, beta_1=0.5), metrics=['accuracy'])
    return model

def def_gan(generator, discriminator):

    # We don't want to train the weights of discriminator at this stage. Hence, make it not trainable
    discriminator.trainable = False

    # Get Generator inputs / outputs
    gen_latent, gen_label = generator.input # Latent and label inputs from the generator
    gen_output = generator.output # Generator output image

    # Connect image and label from the generator to use as input into the discriminator
    gan_output = discriminator([gen_output, gen_label])

    # Define GAN model
    model = Model([gen_latent, gen_label], gan_output, name="cDCGAN")

    # Compile the model
    model.compile(loss='binary_crossentropy', optimizer=Adam(learning_rate=0.0002, beta_1=0.5))
    return model

def real_samples(dataset, categories, n):

    # Create a random list of indices
    indx = np.random.randint(0, dataset.shape[0], n)

    # Select real data samples (images and category labels) using the list of random indeces from above
    X, cat_labels = dataset[indx], categories[indx]

    # Class labels
    y = np.ones((n, 1))
    return [X, cat_labels], y

def latent_vector(latent_dim, n, n_cats=10):

  # Generate points in the latent space
  latent_input = np.random.randn(latent_dim * n)

  # Reshape into a batch of inputs for the network
  latent_input = latent_input.reshape(n, latent_dim)

  # Generate category labels
  cat_labels = np.random.randint(0, n_cats, n)
  return [latent_input, cat_labels]

def fake_samples(generator, latent_dim, n):

    # Draw latent variables
    latent_output, cat_labels = latent_vector(latent_dim, n)

    # Predict outputs (i.e., generate fake samples)
    X = generator.predict([latent_output, cat_labels])

    # Create class labels
    y = np.zeros((n, 1))
    return [X, cat_labels], y

def train(g_model, d_model, gan_model, dataset, categories, latent_dim, n_epochs=1, n_batch=1024, n_eval=200):
  # Number of batches to use per each epoch
  batch_per_epoch = int(dataset.shape[0] / n_batch)
  print(' batch_per_epoch: ', batch_per_epoch)
  # Our batch to train the discriminator will consist of half real images and half fake images
  half_batch = int(n_batch/2)

  # We will manually enumare epochs
  for i in range(n_epochs):
    # Enumerate batches over the training set
    for j in range(batch_per_epoch):

      # Discriminator training
      # Prep real samples
      [x_real, cat_labels_real], y_real = real_samples(dataset, categories, half_batch)
      # Train discriminator with real samples
      discriminator_loss1, _ = d_model.train_on_batch([x_real, cat_labels_real], y_real)

      # Prep fake (generated) sample
      [x_fake, cat_labels_fake], y_fake = fake_samples(g_model, latent_dim, half_batch)
      # Train discriminator with fake samples
      discriminator_loss2, _ = d_model.train_on_batch([x_fake, cat_labels_fake], y_fake)

      # Generator training
      # Get values from the latent space to be used as inputs for the generator
      [latent_input, cat_labels] = latent_vector(latent_dim, n_batch)
      # While we are generating fake samples,
      # we want GAN generator model to create examples that resemble the real ones,
      # hence we want to pass labels corresponding to real samples, i.e. y=1, not 0.
      y_gan = np.ones((n_batch, 1))

      # Train the generator via a composite GAN model
      generator_loss = gan_model.train_on_batch([latent_input, cat_labels], y_gan)

      # Summarize training progress and loss
      if (j) % n_eval == 0:
          print('Epoch: %d, Batch: %d/%d, D_Loss_Real=%.3f, D_Loss_Fake=%.3f Gen_Loss=%.3f' %
                (i+1, j+1, batch_per_epoch, discriminator_loss1, discriminator_loss2, generator_loss))

def generate_dataset(gen_model):
   # We need to compile the generator to avoid a warning. This is because we have previously only copiled within the larger cDCGAN model
   gen_model.compile(loss='binary_crossentropy', optimizer=Adam(learning_rate=0.0002, beta_1=0.5))
   # Save the Generator on your drive
   gen_model.save(main_dir+'/cgan_generator.h5')
   # Generate latent points
   latent_points, _ = latent_vector(100, 10000)

   # Specify labels that we want (0-9 repeated 10 times)
   labels = np.asarray([x for _ in range(1000) for x in range(10)])
   # Load previously saved generator model
   model = load_model(main_dir+'/cgan_generator.h5')

   # Generate images
   gen_imgs  = model.predict([latent_points, labels])
   # Scale from [-1, 1] to [0, 1]
   gen_imgs = (gen_imgs + 1) / 2.0
   np.savez("DCGAN_dataset.npz", images=gen_imgs, labels=labels)
   return

# Load digit data
(X_train, y_train), (_, _) = keras.datasets.mnist.load_data()
# Print shapes
print("Shape of X_train: ", X_train.shape)
print("Shape of y_train: ", y_train.shape)

# Scale and reshape as required by the model
data = X_train.copy()
data = data.reshape(X_train.shape[0], 28, 28, 1)
data = (data - 127.5) / 127.5  # Normalize the images to [-1, 1]
print("Shape of the scaled array: ", data.shape)

# Instantiate
latent_dim=100 # Our latent space has 100 dimensions. We can change it to any number
gen_model = generator(latent_dim)
# Show model summary and plot model diagram
gen_model.summary()

# Instantiate
dis_model = discriminator()
# Show model summary and plot model diagram
dis_model.summary()

# Instantiate
gan_model = def_gan(gen_model, dis_model)
# Show model summary and plot model diagram
gan_model.summary()

train(gen_model, dis_model, gan_model, data, y_train, latent_dim)
generate_dataset(gen_model)

