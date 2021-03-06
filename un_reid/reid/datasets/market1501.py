from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import glob
import re
import os.path as osp
from .bases import BaseImageDataset


class Market1501(BaseImageDataset):
    """
    Market1501

    Reference:
    Zheng et al. Scalable Person Re-identification: A Benchmark. ICCV 2015.

    URL: http://www.liangzheng.org/Project/project_reid.html

    Dataset statistics:
    # identities: 1501 (+1 for background)
    # images: 12936 (train) + 3368 (query) + 15913 (gallery)
    """

    def __init__(self, root='data', verbose=True, **kwargs):
        super(Market1501, self).__init__()
        self.dataset_dir = root
        self.train_dir = osp.join(self.dataset_dir, 'bounding_box_train')
        self.query_dir = osp.join(self.dataset_dir, 'query')
        self.gallery_dir = osp.join(self.dataset_dir, 'bounding_box_test')

        self._check_before_run()

        train = self._struct_data(self.train_dir, relabel=True)
        query = self._struct_data(self.query_dir, relabel=False)
        gallery = self._struct_data(self.gallery_dir, relabel=False)

        if verbose:
            print("=> Market1501 loaded")
            self.print_dataset_statistics(train, query, gallery)

        self.train = train
        self.query = query
        self.gallery = gallery

        self.num_train_pids, self.num_train_imgs, self.num_train_cams, self.num_train_tids_sub = self.get_imagedata_info(self.train)
        self.num_query_pids, self.num_query_imgs, self.num_query_cams, self.num_query_tids_sub = self.get_imagedata_info(self.query)
        self.num_gallery_pids, self.num_gallery_imgs, self.num_gallery_cams, self.num_gallery_tids_sub = self.get_imagedata_info(self.gallery)

    def _check_before_run(self):
        """Check if all files are available before going deeper"""
        if not osp.exists(self.dataset_dir):
            raise RuntimeError("'{}' is not available".format(self.dataset_dir))
        if not osp.exists(self.train_dir):
            raise RuntimeError("'{}' is not available".format(self.train_dir))
        if not osp.exists(self.query_dir):
            raise RuntimeError("'{}' is not available".format(self.query_dir))
        if not osp.exists(self.gallery_dir):
            raise RuntimeError("'{}' is not available".format(self.gallery_dir))

    def _struct_data(self, dir_path, relabel=False):
        img_paths = glob.glob(osp.join(dir_path, '*.jpg'))
        pattern = re.compile(r'([-\d]+)_c(\d)')

        pid_container = set()
        for img_path in img_paths:
            pid, _ = map(int, pattern.search(img_path).groups())
            if pid == -1: continue  # junk images are just ignored
            pid_container.add(pid)
        pid2label = {pid: label for label, pid in enumerate(pid_container)}

        img_dataset = []
        tid = -1
        tid_pc = -1
        pid_pc = -1
        cam_list = []
        for img_path in img_paths:
            pid, camid = map(int, pattern.search(img_path).groups())
            if pid == -1: continue  # junk images are just ignored
            assert 0 <= pid <= 1501  # pid == 0 means background
            assert 1 <= camid <= 6
            camid -= 1  # index starts from 0
            if relabel: pid = pid2label[pid]
            cam_list.append(camid)
            img_dataset.append((img_path, tid, pid, tid_pc, pid_pc, camid))

        tkl_dataset = []
        tid = -1
        cam_list = list(set(cam_list))
        for cam in cam_list:
            tid_index_list = [index for index, (_, _, _, _, _, camid) in enumerate(img_dataset) if camid == cam]
            pid_list_pc = [img_dataset[i][2] for i in tid_index_list]
            unique_pid_list_pc = list(set(pid_list_pc))
            pid_percam2label = {pid: label for label, pid in enumerate(unique_pid_list_pc)}

            for insert_pid in unique_pid_list_pc:
                img_index_list = [index for index, (_, _, pid, _, _, camid) in enumerate(img_dataset) if camid == cam and pid == insert_pid]
                img_names = tuple([osp.join(img_dataset[index][0]) for index in img_index_list])
                pid_pc = pid_percam2label[insert_pid]
                tid_pc = pid_pc
                tid += 1
                pid = insert_pid
                tkl_dataset.append((img_names, tid, pid, tid_pc, pid_pc, cam))
        return tkl_dataset