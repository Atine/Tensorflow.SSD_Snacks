# coding: utf-8
import time

# os imports
import os
import math
import random
import numpy as np

starttime = time.time()
import tensorflow as tf
print ("--- %s seconds ---" % (time.time() - starttime))
import cv2
slim = tf.contrib.slim

# plot imports
#get_ipython().magic(u'matplotlib inline')
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# path imports
import sys
#sys.path.append('../')
sys.path.append('C:/Users/is2017teami/Documents/Tensorflow_SSD_snacks/')

# SSD imports
from nets import ssd_vgg_300, ssd_common, np_methods
from preprocessing import ssd_vgg_preprocessing
import visualization
from nets import nets_factory


### TensorFlow session: grow memory when needed. TF, DO NOT USE ALL MY GPU MEMORY!!!
gpu_options = tf.GPUOptions(allow_growth=True)
config = tf.ConfigProto(log_device_placement=False, gpu_options=gpu_options)
isess = tf.InteractiveSession(config=config)

# ## SSD 300 Model
# 
# The SSD 300 network takes 300x300 image inputs. In order to feed any image, the latter is resize to this input shape 
# (i.e.`Resize.WARP_RESIZE`). Note that even though it may change the ratio width / height, the SSD model performs well 
# on resized images (and it is the default behaviour in the original Caffe implementation).
# SSD anchors correspond to the default bounding boxes encoded in the network. The SSD net output provides offset 
# on the coordinates and dimensions of these anchors.

dataset_name = 'snacks'

assert dataset_name in ['pascalvoc2007', 'pascalvoc2012', 'snacks']
if dataset_name in ['pascalvoc2007', 'pascalvoc2012']:
    num_classes=21
if dataset_name == 'snacks':
    num_classes=8
	
ckpt_filename = 'model.ckpt'
if ckpt_filename == None:
	print ("Checkpoint Path not speficied")
	sys.exit(1)


# Input placeholder.
net_shape = (300, 300)
data_format = 'NHWC'
img_input = tf.placeholder(tf.uint8, shape=(None, None, 3))
# Evaluation pre-processing: resize to SSD net shape.
image_pre, labels_pre, bboxes_pre, bbox_img = ssd_vgg_preprocessing.preprocess_for_eval(
  img_input, None, None, net_shape, data_format, resize=ssd_vgg_preprocessing.Resize.WARP_RESIZE)
image_4d = tf.expand_dims(image_pre, 0)
# Test on some demo image and visualize output.
#path = '../demo/'
#image_names = sorted(os.listdir(path))
#img = mpimg.imread(path + image_names[-5])
#img = mpimg.imread(path + '/IMG_2634.jpg')
#img = mpimg.imread(image_path)

## Define the SSD model.
reuse = True if 'ssd_net' in locals() else None
ssd_net = nets_factory.get_network('ssd_300_vgg')
ssd_params = ssd_net.default_params._replace(num_classes=num_classes, no_annotation_label=num_classes)
ssd_net = ssd_net(ssd_params)

with slim.arg_scope(ssd_net.arg_scope(data_format=data_format)):
  predictions, localizations, _, _ = ssd_net.net(image_4d, is_training=False, reuse=tf.AUTO_REUSE)

## Restore SSD model.
isess.run(tf.global_variables_initializer())
saver = tf.train.Saver()

starttime = time.time()
saver.restore(isess, ckpt_filename)
print ("--- %s seconds ---" % (time.time() - starttime))
ssd_anchors = ssd_net.anchors(net_shape)


  # The SSD outputs need to be post-processed to provide proper detections. Namely, we follow these common steps:
  # 
  # * Select boxes above a classification threshold;
  # * Clip boxes to the image shape;
  # * Apply the Non-Maximum-Selection algorithm: fuse together boxes whose Jaccard score > threshold;
  # * If necessary, resize bounding boxes to original image shape.

#print ("here")
  
def eval_ssd(image_path=None):
  print ('=> Evaluating SSD...')
  if image_path == None:
    print ("Image Path not speficied")
    sys.exit(1)
	
  img = mpimg.imread(image_path)
  # Run SSD network.
  starttime = time.time()
  rimg, rpredictions, rlocalizations, rbbox_img = isess.run([image_4d, predictions, localizations, bbox_img], 
      feed_dict={img_input: img})
  print ("--- %s seconds ---" % (time.time() - starttime))
  
  # Get classes and bboxes from the net outputs.
  rclasses, rscores, rbboxes = np_methods.ssd_bboxes_select(rpredictions, rlocalizations, ssd_anchors,
      select_threshold=0.0, img_shape=net_shape, num_classes=num_classes, decode=True)
  
  rbboxes = np_methods.bboxes_clip(rbbox_img, rbboxes)
  rclasses, rscores, rbboxes = np_methods.bboxes_sort(rclasses, rscores, rbboxes, top_k=400)
  rclasses, rscores, rbboxes = np_methods.bboxes_nms(rclasses, rscores, rbboxes, nms_threshold=0.0)
  # Resize bboxes to original image shape. Note: useless for Resize.WARP!
  rbboxes = np_methods.bboxes_resize(rbbox_img, rbboxes)

  ### visualization.bboxes_draw_on_img(img, rclasses, rscores, rbboxes, visualization.colors_plasma)
  visualization.plt_bboxes(img, rclasses, rscores, rbboxes, dataset_name)
  pred_list = visualization.save_as_JSON(img, rclasses, rscores, rbboxes, dataset_name)
  return pred_list

  
if __name__ == '__main__':

  #ckpt_filename = '../checkpoints/ssd_300_vgg.ckpt'
  #ckpt_filename = '../checkpoints/VGG_VOC0712_SSD_300x300_ft_iter_120000.ckpt'
  ckpt_filename = '../logs8/model.ckpt-22272'

  eval_ssd(dataset_name='snacks', image_path='../demo', ckpt_filename=ckpt_filename)

