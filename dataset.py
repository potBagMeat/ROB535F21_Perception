

import torch
import os
import pandas as pd
import numpy as np
from glob import glob
from PIL import Image
from torchvision import transforms
import ipdb
import time

class GTADataset(torch.utils.data.Dataset):
    def __init__(
            self, label_csv_file, bbox_csv_file, S=7, B=2, C=3, image_size=(448, 448)):
        self.label = pd.read_csv(label_csv_file)
        self.bbox = pd.read_csv(bbox_csv_file)
        self.S = S
        self.B = B
        self.C = C
        self.transform = transforms.Compose([transforms.ToTensor(),])
        self.image_size = image_size
        # self.images = torch.zeros((len(self.label), 3, *image_size))
        #
        # for i, (file_name, label) in enumerate(self.label.values):
        #     image_name = file_name + '_image.jpg'
        #     self.images[i] = Image.open(image_name)

    def __len__(self):
        return len(self.label)

    def __getitem__(self, index):
        t = [time.time()]
        file_name = self.label.iloc[index]['guid/image']
        image_name = '/content/trainval/'+file_name + '_image.jpg'
        image = Image.open(image_name)
        grid_width, grid_height = image.size[0]/self.S, image.size[1]/self.S
        image_width, image_height = image.size
        t.append(time.time())
        if self.transform:
            image = self.transform(image)
            #image = self.transform(image)
        t.append(time.time())

        # Convert To Cells
        label_matrix = torch.zeros((self.S, self.S, self.C + 5 * self.B))
        label_matrix[:,:,0] = torch.ones(label_matrix.shape[0:2], dtype=torch.float)
        name, label = self.label.iloc[index]
        
        if label != 0:
            x, y, w, h = self.bbox[self.bbox['guid/image'] == name].iloc[0][1:]
            #x = x / image_width * self.image_size[0]
            #w = w / image_width * self.image_size[0]
            #y = y / image_height * self.image_size[1]
            #h = h / image_height * self.image_size[1]
            idx_x = int(x//grid_width)
            idx_y = int(y//grid_height)
            label_matrix[idx_x][idx_y][0] = 0.0
            label_matrix[idx_x][idx_y][label] = 1.0
            label_matrix[idx_x][idx_y][self.C] = 1.0
            label_matrix[idx_x][idx_y][self.C+5] = 1.0
            norm_x =(x - idx_x * grid_width) / grid_width
            norm_y =(y - idx_y * grid_height) / grid_height
            norm_w = w / grid_width
            norm_h = h / grid_height
            label_matrix[idx_x][idx_y][self.C+1 : self.C+5] = torch.tensor([norm_x, norm_y, norm_w, norm_h])
            label_matrix[idx_x][idx_y][self.C+6 : self.C+10] = torch.tensor([norm_x, norm_y, norm_w, norm_h])
        t.append(time.time())
        dt = []
        for i in range(len(t)-1):
            dt.append(t[i+1]-t[i])
        return image, label_matrix

if __name__=='__main__':
    dataset = GTADataset('./data/trainval/trainval_labels.csv', 'data/trainval/trainval_bboxes.csv')
