import os
import cv2
import tensorflow as tf
import keras_preprocessing
import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image

from utils import label_map_util
from utils import visualization_utils as vis_util
from keras.preprocessing import image
from keras_preprocessing.image import ImageDataGenerator


# Set up default variables
MODEL_NAME = 'model'
PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'
PATH_TO_LABELS = 'object-detection1.pbtxt'
PATH_TO_IMAGE = 'images/out.png'
CWD_PATH = os.getcwd()
NUM_CLASSES = 4

label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)

@st.cache
def detect():
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')
        sess = tf.Session(graph=detection_graph)

    # Input tensor is the image
    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
    # Output tensors are the detection boxes, scores, and classes
    # Each score represents level of confidence for each of the objects.
    # The score is shown on the result image, together with the class label.
    detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
    detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
    detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
    # Number of objects detected
    num_detections = detection_graph.get_tensor_by_name('num_detections:0')

    # Load image using OpenCV and
    # expand image dimensions to have shape: [1, None, None, 3]
    # i.e. a single-column array, where each item in the column has the pixel RGB value
    in_image = cv2.imread(PATH_TO_IMAGE)
    image_rgb = cv2.cvtColor(in_image, cv2.COLOR_BGR2RGB)
    image_expanded = np.expand_dims(
        image_rgb, axis=0)

    # Perform the actual detection by running the model with the image as input
    (boxes, scores, classes, num) = sess.run(
        [detection_boxes, detection_scores, detection_classes, num_detections],
        feed_dict={image_tensor: image_expanded})

    # Draw the results of the detection (aka 'visulaize the results')
    vis_util.visualize_boxes_and_labels_on_image_array(
        in_image,
        np.squeeze(boxes),
        np.squeeze(classes).astype(np.int32),
        np.squeeze(scores),
        category_index,
        use_normalized_coordinates=True,
        line_thickness=8,
        min_score_thresh=0.50)

    return in_image

def main():
    st.title("MEP Object Detection 👁")
    #Disable warnings
    st.set_option('deprecation.showfileUploaderEncoding', False)
    st.write("This application detects Mechanical, Electrical and Plumbing assets in images.")
    st.write("## How does it work?")
    st.write("Upload an image of a room and the deep learning learning model will interrogate it to find MEP assets. It currently supports sockets, switches and radiators")
    st.write("## Upload your own image")
    st.write("**Note:** The model has been trained on typical classrooms and household rooms and will therefore work best for those use cases.")
    uploaded_image = st.file_uploader("Choose a png or jpg image",
                                      type=["jpg", "png", "jpeg"])

    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        im = image.save('images/out.png')
        # Make sure image is RGB
        # TODO: If image is over certain size resize image to certain size

        if st.button("Make a prediction"):
          "Making a prediction and drawing MEP boxes on your image..."
          with st.spinner("Doing the math..."):
            st.image(detect(), caption="MEP assets detected.", use_column_width=True)

        st.image(image, caption="Uploaded Image.", use_column_width=True)

    st.write("## How is this made?")
    st.write("A [Faster R-CNN](https://arxiv.org/abs/1506.01497?source=post_page) model is used to perform the detections, \
    this front end (what you're reading) is built with [Streamlit](https://www.streamlit.io/) \
    and it's all hosted on [Heroku](https://www.heroku.com/).")
    st.write("See the [code on GitHub](https://github.com/Jam516/MEP-detection-app)")

if __name__ == "__main__":
    main()
