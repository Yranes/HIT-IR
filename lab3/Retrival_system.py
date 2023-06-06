import os
import sys
from time import time

from utils import Search
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

page_header = ['页面标题', '页面正文', '权限要求']
file_header = ['文件名', '所属页面', '文件内容', '权限要求']
authority = ['级别 1', '级别 2', '级别 3', '级别 4']


class Retrieval(QWidget):
    def __init__(self, table, search, mode):
        super().__init__()
        self.mode = mode
        self.setWindowTitle('企业检索系统')
        self.search_button = QPushButton('查询')
        self.clear_table_button = QPushButton('清空表单')
        self.search_button.setShortcut(Qt.Key_Return)
        self.clear_table_button.setShortcut(Qt.Key_Down)
        self.input_box = QLineEdit(self)
        self.search_result_label = QLabel(self)
        self.combo = QComboBox()
        self.table = table
        self._setup()
        self.lines = []
        self.search = search
        self.show()

    def _clear_table(self):
        self.table.setRowCount(0)
        self.table.clearContents()

    def _setup(self):
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.input_box)
        search_layout.addWidget(self.combo)
        search_layout.addWidget(self.clear_table_button)

        window_layout = QVBoxLayout()
        window_layout.addLayout(search_layout)
        window_layout.addWidget(self.search_button)
        window_layout.addWidget(self.table)
        window_layout.addWidget(self.search_result_label)

        self.setLayout(window_layout)
        self.search_button.clicked.connect(self.__search)
        self.clear_table_button.clicked.connect(self._clear_table)
        self.combo.addItems(authority)
        self.table.itemDoubleClicked.connect(self.__open)

    def get_role(self):
        role = self.combo.currentText()
        return int(role[-1])

    def __search(self):
        Has_exist, row = set(), 0
        query = self.input_box.text()
        self.table.clear()
        if self.mode == 'page':
            self.table.setHorizontalHeaderLabels(page_header)
        else:
            self.table.setHorizontalHeaderLabels(file_header)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionsClickable(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        start_time = time()
        self.lines = self.search.search(query, self.get_role(), self.mode)
        end_time = time()
        self.table.setRowCount(len(self.lines))
        if self.mode == 'page':
            for data in self.lines:
                if data['title'] not in Has_exist:
                    Has_exist.add(data['title'])
                    self.table.setItem(row, 0, QTableWidgetItem(data['title'].replace(' ', '')))
                    self.table.setItem(row, 1, QTableWidgetItem((''.join(data['paragraghs'][:15])).replace(' ', '')))
                    self.table.setItem(row, 2, QTableWidgetItem('权限等级{:d}'.format(data['authority'])))
                    row += 1
        else:
            for file in self.lines:
                if file[0] not in Has_exist:
                    Has_exist.add(file[0])
                    self.table.setItem(row, 0, QTableWidgetItem(file[0]))
                    self.table.setItem(row, 1, QTableWidgetItem(file[1]))
                    self.table.setItem(row, 2, QTableWidgetItem(file[2]))
                    self.table.setItem(row, 3, QTableWidgetItem('权限等级{:d}'.format(file[3])))
                    row += 1
        self.search_result_label.setText('找到 {:d} 条结果, 耗时 {:.4f}s'.format(len(self.lines), end_time - start_time))

    def __open(self, item):
        if self.mode == 'page':
            pos = item.row()
            data = self.lines[pos]
            os.system('chcp 65001')
            os.system('explorer ' + data['url'])
        else:
            pos = item.row()
            data = self.lines[pos]
            file_name = data[0]
            if '.docx' not in file_name:
                file_name += 'x'
            os.system('chcp 65001')
            os.system('cd ./file/ && start '+ file_name)

class RetrievalSystem(QTabWidget):

    def __init__(self):
        super(RetrievalSystem, self).__init__()
        self.setWindowTitle('企业检索系统')

        self.resize(520, 520)

        table1 = QTableWidget(self)
        table1.setColumnCount(3)
        table1.setHorizontalHeaderLabels(page_header)

        table2 = QTableWidget(self)
        table2.setColumnCount(4)
        table2.setHorizontalHeaderLabels(file_header)

        search = Search()
        self.tab1 = Retrieval(table1, search, 'page')
        self.tab2 = Retrieval(table2, search, 'file')
        self.addTab(self.tab1, "页面检索")
        self.addTab(self.tab2, "文档检索")
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RetrievalSystem()
    ex.setWindowIcon(QIcon("./data/IR.jpg"))
    sys.exit(app.exec_())