import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, 
                             QVBoxLayout, QHBoxLayout, QLabel, QWidget, QProgressBar,
                             QListWidget, QMessageBox, QGroupBox, QCheckBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import asyncio
from playwright.async_api import async_playwright

class ConversionWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, html_files, output_dir, use_fullpage, custom_wait):
        super().__init__()
        self.html_files = html_files
        self.output_dir = output_dir
        self.use_fullpage = use_fullpage
        self.custom_wait = custom_wait  # 等待时间(毫秒)
        
    def run(self):
        asyncio.run(self.convert_files())
        
    async def convert_files(self):
        try:
            async with async_playwright() as p:
                # 使用带有更好渲染能力的Chromium浏览器
                browser = await p.chromium.launch(
                    args=['--disable-web-security', '--allow-file-access-from-files']
                )
                
                for i, html_file in enumerate(self.html_files):
                    try:
                        context = await browser.new_context()
                        
                        # 创建一个新页面，大尺寸视窗
                        page = await context.new_page()
                        await page.set_viewport_size({"width": 1280, "height": 1600})
                        
                        # 获取HTML文件的完整路径和文件URL
                        file_path = os.path.abspath(html_file)
                        file_url = f"file://{file_path}"
                        
                        # 导航到HTML文件
                        await page.goto(file_url, wait_until="networkidle", timeout=90000)
                        
                        # 等待JavaScript完全加载
                        await page.wait_for_load_state("domcontentloaded")
                        await page.wait_for_timeout(self.custom_wait)  # 用户定义的等待时间
                        
                        # 确定输出文件名
                        base_name = os.path.basename(html_file)
                        pdf_name = os.path.splitext(base_name)[0] + ".pdf"
                        output_path = os.path.join(self.output_dir, pdf_name)
                        
                        if self.use_fullpage:
                            # 使用完整页面转换方式 - 通过截取完整高度的方式
                            # 先获取完整的页面高度
                            height = await page.evaluate('''
                                () => {
                                    // 获取全部内容的高度，检查所有可能定义高度的元素
                                    return Math.max(
                                        document.body.scrollHeight,
                                        document.body.offsetHeight,
                                        document.documentElement.scrollHeight,
                                        document.documentElement.offsetHeight,
                                        document.documentElement.clientHeight,
                                        document.body.clientHeight,
                                        // 额外检查所有固定高度的容器
                                        ...Array.from(document.querySelectorAll('*')).map(el => el.scrollHeight)
                                    );
                                }
                            ''')
                            
                            # 确保我们有一个合理的高度，设置最小高度
                            height = max(height, 1100)
                            
                            # 设置页面大小以包含全部内容
                            await page.set_viewport_size({"width": 1280, "height": height + 200})
                            
                            # 再次等待以确保新尺寸能够正确生效
                            await page.wait_for_timeout(300)
                            
                            # 使用自定义尺寸生成PDF
                            await page.pdf(
                                path=output_path,
                                print_background=True,
                                format=None,  # 不使用预定义格式
                                width="1280px",
                                height=f"{height + 100}px",
                                margin={"top": "20px", "right": "20px", "bottom": "20px", "left": "20px"},
                                scale=0.9  # 缩小一点以确保内容都能放进去
                            )
                        else:
                            # 使用更可靠的方法：处理所有分页内容
                            await page.pdf(
                                path=output_path,
                                print_background=True,
                                prefer_css_page_size=True,  # 尊重CSS页面大小设置
                                format="A4",
                                margin={"top": "20px", "right": "20px", "bottom": "20px", "left": "20px"},
                                scale=0.9,  # 缩小一点以确保内容都能放进去
                            )
                        
                        await context.close()
                        
                        # 更新进度
                        self.progress.emit(int((i + 1) / len(self.html_files) * 100))
                    
                    except Exception as e:
                        self.error.emit(f"处理文件 {html_file} 时出错: {str(e)}")
                
                await browser.close()
                self.finished.emit()
                
        except Exception as e:
            self.error.emit(f"转换过程中发生错误: {str(e)}")

class HTMLtoPDFConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.html_files = []
        
    def initUI(self):
        self.setWindowTitle('HTMLtoPDF Converter_v1.0')
        self.setGeometry(300, 300, 800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f7;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 6px;
                margin-top: 12px;
                font-weight: bold;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 20px;
            }
            QLabel {
                font-size: 14px;
            }
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QCheckBox {
                font-size: 13px;
            }
        """)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel('HTML 批量转 PDF 工具')
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #333333;
            margin-bottom: 10px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 文件选择区域
        input_group = QGroupBox("输入文件")
        input_layout = QVBoxLayout()
        
        html_layout = QHBoxLayout()
        self.html_label = QLabel('HTML文件:')
        self.select_html_btn = QPushButton('选择HTML文件')
        self.select_html_btn.setFixedHeight(40)
        self.select_html_btn.clicked.connect(self.selectHTMLFiles)
        html_layout.addWidget(self.html_label)
        html_layout.addStretch()
        html_layout.addWidget(self.select_html_btn)
        input_layout.addLayout(html_layout)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("font-size: 13px;")
        self.file_list.setAlternatingRowColors(True)
        input_layout.addWidget(self.file_list)
        
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # 输出区域
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout()
        
        output_path_layout = QHBoxLayout()
        self.output_label = QLabel('输出目录:')
        self.output_path_label = QLabel('未选择')
        self.output_path_label.setStyleSheet("""
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 5px;
            background-color: #f9f9f9;
        """)
        self.select_output_btn = QPushButton('选择输出目录')
        self.select_output_btn.setFixedHeight(40)
        self.select_output_btn.clicked.connect(self.selectOutputDir)
        output_path_layout.addWidget(self.output_label)
        output_path_layout.addWidget(self.output_path_label, 1)
        output_path_layout.addWidget(self.select_output_btn)
        output_layout.addLayout(output_path_layout)
        
        # 添加高级设置区域
        advanced_layout = QHBoxLayout()
        
        # 完整页面选项
        self.fullpage_checkbox = QCheckBox("使用完整页面模式（推荐用于长页面）")
        self.fullpage_checkbox.setChecked(True)
        advanced_layout.addWidget(self.fullpage_checkbox)
        
        # 等待时间设置
        wait_label = QLabel("页面加载等待时间(毫秒):")
        self.wait_time_label = QLabel("2000")
        self.wait_time_label.setStyleSheet("""
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 5px;
            background-color: #f9f9f9;
            min-width: 60px;
            text-align: center;
        """)
        self.decrease_wait_btn = QPushButton("-")
        self.decrease_wait_btn.setFixedSize(30, 30)
        self.decrease_wait_btn.clicked.connect(self.decreaseWaitTime)
        
        self.increase_wait_btn = QPushButton("+")
        self.increase_wait_btn.setFixedSize(30, 30)
        self.increase_wait_btn.clicked.connect(self.increaseWaitTime)
        
        wait_layout = QHBoxLayout()
        wait_layout.addWidget(wait_label)
        wait_layout.addWidget(self.decrease_wait_btn)
        wait_layout.addWidget(self.wait_time_label)
        wait_layout.addWidget(self.increase_wait_btn)
        wait_layout.addStretch()
        
        advanced_layout.addLayout(wait_layout)
        output_layout.addLayout(advanced_layout)
        
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # 进度区域
        progress_group = QGroupBox("转换进度")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(30)
        progress_layout.addWidget(self.progress_bar)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # 转换按钮
        self.convert_btn = QPushButton('开始转换')
        self.convert_btn.setFixedHeight(50)
        self.convert_btn.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            background-color: #4CAF50;
        """)
        self.convert_btn.clicked.connect(self.startConversion)
        self.convert_btn.setEnabled(False)
        main_layout.addWidget(self.convert_btn)
        
        # 状态信息
        self.status_label = QLabel('准备就绪')
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # 设置主窗口部件
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
    def decreaseWaitTime(self):
        current = int(self.wait_time_label.text())
        if current > 500:
            self.wait_time_label.setText(str(current - 500))
    
    def increaseWaitTime(self):
        current = int(self.wait_time_label.text())
        self.wait_time_label.setText(str(current + 500))
    
    def selectHTMLFiles(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择HTML文件", "", "HTML Files (*.html *.htm)")
        if files:
            self.html_files = files
            self.file_list.clear()
            for file in files:
                self.file_list.addItem(os.path.basename(file))
            self.status_label.setText(f"已选择 {len(files)} 个HTML文件")
            self.checkConvertButton()
    
    def selectOutputDir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_path_label.setText(directory)
            self.status_label.setText(f"输出目录: {directory}")
            self.checkConvertButton()
    
    def checkConvertButton(self):
        # 检查是否可以启用转换按钮
        if self.html_files and self.output_path_label.text() != '未选择':
            self.convert_btn.setEnabled(True)
            self.status_label.setText("可以开始转换")
        else:
            self.convert_btn.setEnabled(False)
    
    def startConversion(self):
        # 禁用界面元素
        self.convert_btn.setEnabled(False)
        self.select_html_btn.setEnabled(False)
        self.select_output_btn.setEnabled(False)
        self.status_label.setText("正在转换中...")
        
        # 初始化并启动工作线程
        use_fullpage = self.fullpage_checkbox.isChecked()
        wait_time = int(self.wait_time_label.text())
        
        self.worker = ConversionWorker(
            self.html_files, 
            self.output_path_label.text(),
            use_fullpage,
            wait_time
        )
        self.worker.progress.connect(self.updateProgress)
        self.worker.finished.connect(self.conversionFinished)
        self.worker.error.connect(self.showError)
        self.worker.start()
    
    def updateProgress(self, value):
        self.progress_bar.setValue(value)
        self.status_label.setText(f"转换进度: {value}%")
    
    def conversionFinished(self):
        # 重新启用界面元素
        self.convert_btn.setEnabled(True)
        self.select_html_btn.setEnabled(True)
        self.select_output_btn.setEnabled(True)
        self.status_label.setText("转换完成！")
        
        # 显示完成消息并提供打开输出目录的选项
        reply = QMessageBox.information(
            self, 
            "转换完成", 
            f"{len(self.html_files)}个HTML文件已成功转换为PDF！\n\n输出目录: {self.output_path_label.text()}\n\n如果内容不完整，请尝试:\n1. 增加等待时间\n2. 确保选中\"完整页面模式\"选项", 
            QMessageBox.Ok | QMessageBox.Open,
            QMessageBox.Ok
        )
        
        # 如果用户点击"打开"按钮，则打开输出目录
        if reply == QMessageBox.Open:
            os.startfile(self.output_path_label.text())
    
    def showError(self, message):
        QMessageBox.critical(self, "错误", message)
        # 重新启用界面元素
        self.convert_btn.setEnabled(True)
        self.select_html_btn.setEnabled(True)
        self.select_output_btn.setEnabled(True)
        self.status_label.setText("转换过程中发生错误")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion风格获得更现代的外观
    converter = HTMLtoPDFConverter()
    converter.show()
    sys.exit(app.exec_())