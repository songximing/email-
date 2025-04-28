import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import imaplib
import poplib
import email
import os
import json
from datetime import datetime, timedelta
from dateutil import parser
from tqdm import tqdm
import threading

class EmailAttachmentDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("邮件附件下载器")
        self.root.geometry("600x600")  # 增加窗口高度以容纳日期选择
        self.root.resizable(True, True)
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建配置框架
        self.create_config_frame()
        
        # 创建日期选择框架
        self.create_date_frame()
        
        # 创建保存路径框架
        self.create_save_path_frame()
        
        # 创建按钮框架
        self.create_button_frame()
        
        # 创建日志框架
        self.create_log_frame()
        
        # 加载保存的配置
        self.load_config()
        
        # 添加下载器实例变量
        self.downloader = None
        
    def create_config_frame(self):
        config_frame = ttk.LabelFrame(self.main_frame, text="邮箱配置", padding="5")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 协议选择
        ttk.Label(config_frame, text="协议:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.protocol_var = tk.StringVar(value="IMAP")
        protocol_combo = ttk.Combobox(config_frame, textvariable=self.protocol_var, values=["IMAP", "POP3"])
        protocol_combo.grid(row=0, column=1, sticky=tk.W, pady=2)
        protocol_combo.bind('<<ComboboxSelected>>', self.on_protocol_change)
        
        # 邮箱地址
        ttk.Label(config_frame, text="邮箱地址:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.email_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.email_var, width=40).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # 密码
        ttk.Label(config_frame, text="密码/授权码:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.password_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.password_var, show="*", width=40).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # 服务器
        ttk.Label(config_frame, text="服务器:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.server_var = tk.StringVar(value="imap.gmail.com")
        ttk.Entry(config_frame, textvariable=self.server_var, width=40).grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # 服务器选择下拉框
        self.server_options = {
            "IMAP": {
                "Gmail": "imap.gmail.com",
                "Outlook": "outlook.office365.com",
                "QQ邮箱": "imap.qq.com",
                "163邮箱": "imap.163.com",
                "企业163邮箱": "imap.qiye.163.com"
            },
            "POP3": {
                "Gmail": "pop.gmail.com",
                "Outlook": "outlook.office365.com",
                "QQ邮箱": "pop.qq.com",
                "163邮箱": "pop.163.com",
                "企业163邮箱": "pop.qiye.163.com"
            }
        }
        self.server_type_var = tk.StringVar()
        ttk.Label(config_frame, text="快速选择:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.server_combo = ttk.Combobox(config_frame, textvariable=self.server_type_var, 
                                       values=list(self.server_options["IMAP"].keys()))
        self.server_combo.grid(row=4, column=1, sticky=tk.W, pady=2)
        self.server_combo.bind('<<ComboboxSelected>>', self.on_server_select)
        
    def on_protocol_change(self, event):
        protocol = self.protocol_var.get()
        self.server_combo['values'] = list(self.server_options[protocol].keys())
        self.server_type_var.set("")
        self.server_var.set("")
        
    def on_server_select(self, event):
        protocol = self.protocol_var.get()
        selected_server = self.server_type_var.get()
        if selected_server in self.server_options[protocol]:
            self.server_var.set(self.server_options[protocol][selected_server])
            
    def create_date_frame(self):
        date_frame = ttk.LabelFrame(self.main_frame, text="时间范围", padding="5")
        date_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 开始日期
        ttk.Label(date_frame, text="开始日期:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.start_date = DateEntry(date_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2)
        self.start_date.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # 结束日期
        ttk.Label(date_frame, text="结束日期:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.end_date = DateEntry(date_frame, width=12, background='darkblue',
                                foreground='white', borderwidth=2)
        self.end_date.grid(row=0, column=3, sticky=tk.W, pady=2)
        
        # 设置默认日期（最近一个月）
        today = datetime.now()
        self.end_date.set_date(today)
        self.start_date.set_date(today - timedelta(days=30))
        
    def create_info_frame(self):
        # 移除日期选择框架，改为显示提示信息
        info_frame = ttk.LabelFrame(self.main_frame, text="下载说明", padding="5")
        info_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        info_text = "将下载邮箱中的所有附件，按发件人分类保存"
        ttk.Label(info_frame, text=info_text).grid(row=0, column=0, sticky=tk.W, pady=2)
        
    def create_save_path_frame(self):
        path_frame = ttk.LabelFrame(self.main_frame, text="保存路径", padding="5")
        path_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.save_path_var = tk.StringVar(value="attachments")
        ttk.Entry(path_frame, textvariable=self.save_path_var, width=50).grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        ttk.Button(path_frame, text="浏览", command=self.browse_save_path).grid(row=0, column=1, sticky=tk.W, pady=2)
        
    def create_button_frame(self):
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(button_frame, text="开始下载", command=self.start_download).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="保存配置", command=self.save_config).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="清除日志", command=self.clear_log).grid(row=0, column=2, padx=5)
        
    def create_log_frame(self):
        log_frame = ttk.LabelFrame(self.main_frame, text="下载日志", padding="5")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 创建日志文本框
        self.log_text = tk.Text(log_frame, height=10, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text['yscrollcommand'] = scrollbar.set
        
        # 配置网格权重
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(4, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def browse_save_path(self):
        path = filedialog.askdirectory()
        if path:
            self.save_path_var.set(path)
            
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        
    def save_config(self):
        config = {
            "email": self.email_var.get(),
            "server": self.server_var.get(),
            "save_path": self.save_path_var.get()
        }
        with open("email_config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        self.log("配置已保存")
        
    def load_config(self):
        try:
            with open("email_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                self.email_var.set(config.get("email", ""))
                self.server_var.set(config.get("server", "imap.gmail.com"))
                self.save_path_var.set(config.get("save_path", "attachments"))
        except FileNotFoundError:
            pass
            
    def start_download(self):
        # 验证输入
        if not self.email_var.get() or not self.password_var.get():
            messagebox.showerror("错误", "请填写邮箱地址和密码")
            return
            
        # 验证日期
        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()
        if start_date > end_date:
            messagebox.showerror("错误", "开始日期不能晚于结束日期")
            return
            
        # 创建下载器实例
        protocol = self.protocol_var.get()
        if protocol == "IMAP":
            self.downloader = IMAPAttachmentDownloader(
                self.email_var.get(),
                self.password_var.get(),
                self.server_var.get()
            )
        else:  # POP3
            self.downloader = POP3AttachmentDownloader(
                self.email_var.get(),
                self.password_var.get(),
                self.server_var.get()
            )
        
        # 连接服务器并获取邮件数量
        if not self.downloader.connect():
            self.log("连接失败")
            return
            
        try:
            # 获取邮件总数
            if protocol == "IMAP":
                self.downloader.mail.select('INBOX')
                # 构建日期搜索条件
                start_str = start_date.strftime("%d-%b-%Y")
                end_str = end_date.strftime("%d-%b-%Y")
                # 使用更简单的搜索条件
                search_criteria = f'SINCE {start_str} BEFORE {end_str}'
                print(f"搜索条件: {search_criteria}")  # 添加调试信息
                _, message_numbers = self.downloader.mail.uid('search', None, search_criteria)
                total_messages = len(message_numbers[0].split())
            else:  # POP3
                # POP3不支持按日期搜索，只能获取所有邮件
                total_messages = len(self.downloader.mail.list()[1])
                
            # 显示确认对话框
            confirm = messagebox.askyesno(
                "确认下载",
                f"已找到 {total_messages} 封邮件，是否开始下载附件？\n\n"
                "注意：下载过程可能需要较长时间，请耐心等待。"
            )
            
            if confirm:
                # 在新线程中运行下载
                thread = threading.Thread(target=self.run_download, args=(self.downloader, start_date, end_date))
                thread.daemon = True
                thread.start()
            else:
                self.downloader.close()
                self.log("已取消下载")
                
        except Exception as e:
            self.log(f"获取邮件数量失败: {str(e)}")
            if self.downloader:
                self.downloader.close()
                
    def run_download(self, downloader, start_date, end_date):
        try:
            self.log("开始下载附件...")
            downloader.download_attachments(self.save_path_var.get(), start_date, end_date)
            self.log("下载完成！")
        except Exception as e:
            self.log(f"下载过程中出错: {str(e)}")
        finally:
            downloader.close()

class POP3AttachmentDownloader:
    def __init__(self, email_address, password, pop3_server="pop.gmail.com", pop3_port=995):
        self.email_address = email_address
        self.password = password
        self.pop3_server = pop3_server
        self.pop3_port = pop3_port
        self.mail = None

    def connect(self):
        try:
            self.mail = poplib.POP3_SSL(self.pop3_server, self.pop3_port)
            self.mail.user(self.email_address)
            self.mail.pass_(self.password)
            return True
        except Exception as e:
            print(f"连接失败: {str(e)}")
            return False

    def download_attachments(self, save_dir="attachments", start_date=None, end_date=None):
        if not self.mail:
            print("未连接到邮件服务器")
            return

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        try:
            # 获取邮件总数
            message_count = len(self.mail.list()[1])
            print(f"找到 {message_count} 封邮件")

            # 设置每批处理的邮件数量
            batch_size = 500  # 批处理大小
            total_batches = (message_count + batch_size - 1) // batch_size

            for batch in range(total_batches):
                start_idx = batch * batch_size + 1
                end_idx = min((batch + 1) * batch_size, message_count)
                
                print(f"正在处理第 {batch + 1}/{total_batches} 批邮件 ({start_idx}-{end_idx})")
                
                for i in tqdm(range(start_idx, end_idx + 1), desc=f"批次 {batch + 1}"):
                    try:
                        # 获取邮件
                        response, lines, octets = self.mail.retr(i)
                        email_body = b'\r\n'.join(lines)
                        message = email.message_from_bytes(email_body)

                        subject = self._decode_email_header(message.get('subject', 'No Subject'))
                        date = message.get('date', 'No Date')
                        from_addr = self._decode_email_header(message.get('from', 'Unknown'))
                        
                        # 检查邮件日期是否在指定范围内
                        try:
                            email_date = parser.parse(date)
                            if start_date and end_date:
                                if not (start_date <= email_date.date() <= end_date):
                                    continue
                        except:
                            pass  # 如果日期解析失败，继续处理
                        
                        # 提取发件人用户名
                        if '<' in from_addr and '>' in from_addr:
                            display_name = from_addr[:from_addr.find('<')].strip()
                            email_address = from_addr[from_addr.find('<')+1:from_addr.find('>')]
                            username = display_name if display_name else email_address.split('@')[0]
                        else:
                            username = from_addr.split('@')[0]
                        
                        # 清理用户名，移除非法字符
                        sender_folder = self._clean_folder_name(username)

                        has_attachment = False
                        for part in message.walk():
                            if part.get_content_maintype() == 'multipart':
                                continue
                            if part.get('Content-Disposition') is None:
                                continue

                            filename = part.get_filename()
                            if filename:
                                has_attachment = True
                                filename = self._decode_email_header(filename)
                                # 使用发件人用户名创建子文件夹
                                subfolder = os.path.join(save_dir, sender_folder)
                                if not os.path.exists(subfolder):
                                    os.makedirs(subfolder)

                                # 添加日期到文件名前
                                try:
                                    email_date = parser.parse(date).strftime("%Y%m%d")
                                except:
                                    email_date = "00000000"  # 如果日期解析失败，使用默认值
                                new_filename = f"{email_date}_{filename}"
                                
                                filepath = os.path.join(subfolder, new_filename)
                                with open(filepath, 'wb') as f:
                                    f.write(part.get_payload(decode=True))
                                print(f"\n已保存附件: {filepath}")

                        if not has_attachment:
                            print(f"\n跳过无附件邮件: {subject}")

                    except Exception as e:
                        print(f"\n处理邮件时出错: {str(e)}")
                        continue

        except Exception as e:
            print(f"获取邮件失败: {str(e)}")
            return

    def _decode_email_header(self, header):
        if header is None:
            return ""
        decoded_header = email.header.decode_header(header)
        return "".join([
            str(t[0], t[1] if t[1] else 'utf-8') if isinstance(t[0], bytes) else str(t[0])
            for t in decoded_header
        ])

    def _clean_folder_name(self, name):
        """清理文件夹名称，移除非法字符"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        if len(name) > 50:
            name = name[:50]
        return name

    def close(self):
        if self.mail:
            self.mail.quit()

class IMAPAttachmentDownloader:
    def __init__(self, email_address, password, imap_server="imap.gmail.com", imap_port=993):
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.mail = None

    def connect(self):
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mail.login(self.email_address, self.password)
            return True
        except Exception as e:
            print(f"连接失败: {str(e)}")
            return False

    def download_attachments(self, save_dir="attachments", start_date=None, end_date=None):
        if not self.mail:
            print("未连接到邮件服务器")
            return

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        self.mail.select('INBOX')
        
        try:
            # 构建日期搜索条件
            if start_date and end_date:
                start_str = start_date.strftime("%d-%b-%Y")
                end_str = end_date.strftime("%d-%b-%Y")
                # 使用更简单的搜索条件
                search_criteria = f'SINCE {start_str} BEFORE {end_str}'
                print(f"搜索条件: {search_criteria}")  # 添加调试信息
            else:
                search_criteria = 'ALL'
                
            # 获取邮件的UID
            _, message_numbers = self.mail.uid('search', None, search_criteria)
            message_uids = message_numbers[0].split()
            total_messages = len(message_uids)
            print(f"找到 {total_messages} 封邮件")

            # 设置每批处理的邮件数量
            batch_size = 2500  # 批处理大小
            total_batches = (total_messages + batch_size - 1) // batch_size

            for batch in range(total_batches):
                start_idx = batch * batch_size
                end_idx = min((batch + 1) * batch_size, total_messages)
                
                # 获取当前批次的UID
                batch_uids = message_uids[start_idx:end_idx]
                
                print(f"正在处理第 {batch + 1}/{total_batches} 批邮件 ({start_idx + 1}-{end_idx})")
                
                for uid in tqdm(batch_uids, desc=f"批次 {batch + 1}"):
                    try:
                        # 使用UID获取邮件
                        _, msg_data = self.mail.uid('fetch', uid, '(RFC822)')
                        if not msg_data or not msg_data[0]:
                            continue
                            
                        email_body = msg_data[0][1]
                        message = email.message_from_bytes(email_body)

                        subject = self._decode_email_header(message.get('subject', 'No Subject'))
                        date = message.get('date', 'No Date')
                        from_addr = self._decode_email_header(message.get('from', 'Unknown'))
                        
                        # 检查邮件日期是否在指定范围内
                        try:
                            email_date = parser.parse(date)
                            print(f"邮件日期: {email_date}")  # 添加调试信息
                            if start_date and end_date:
                                if not (start_date <= email_date.date() <= end_date):
                                    print(f"跳过日期范围外的邮件: {email_date.date()}")  # 添加调试信息
                                    continue
                        except Exception as e:
                            print(f"日期解析失败: {str(e)}")  # 添加调试信息
                            pass  # 如果日期解析失败，继续处理
                        
                        # 提取发件人用户名
                        if '<' in from_addr and '>' in from_addr:
                            display_name = from_addr[:from_addr.find('<')].strip()
                            email_address = from_addr[from_addr.find('<')+1:from_addr.find('>')]
                            username = display_name if display_name else email_address.split('@')[0]
                        else:
                            username = from_addr.split('@')[0]
                        
                        # 清理用户名，移除非法字符
                        sender_folder = self._clean_folder_name(username)

                        has_attachment = False
                        for part in message.walk():
                            if part.get_content_maintype() == 'multipart':
                                continue
                            if part.get('Content-Disposition') is None:
                                continue

                            filename = part.get_filename()
                            if filename:
                                has_attachment = True
                                filename = self._decode_email_header(filename)
                                # 使用发件人用户名创建子文件夹
                                subfolder = os.path.join(save_dir, sender_folder)
                                if not os.path.exists(subfolder):
                                    os.makedirs(subfolder)

                                # 添加日期到文件名前
                                try:
                                    email_date = parser.parse(date).strftime("%Y%m%d")
                                except:
                                    email_date = "00000000"  # 如果日期解析失败，使用默认值
                                new_filename = f"{email_date}_{filename}"
                                
                                filepath = os.path.join(subfolder, new_filename)
                                with open(filepath, 'wb') as f:
                                    f.write(part.get_payload(decode=True))
                                print(f"\n已保存附件: {filepath}")

                        if not has_attachment:
                            print(f"\n跳过无附件邮件: {subject}")

                    except Exception as e:
                        print(f"\n处理邮件时出错: {str(e)}")
                        continue

        except Exception as e:
            print(f"搜索邮件失败: {str(e)}")
            return

    def _decode_email_header(self, header):
        if header is None:
            return ""
        decoded_header = email.header.decode_header(header)
        return "".join([
            str(t[0], t[1] if t[1] else 'utf-8') if isinstance(t[0], bytes) else str(t[0])
            for t in decoded_header
        ])

    def _clean_folder_name(self, name):
        """清理文件夹名称，移除非法字符"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        if len(name) > 50:
            name = name[:50]
        return name

    def close(self):
        if self.mail:
            self.mail.close()
            self.mail.logout()

if __name__ == "__main__":
    root = tk.Tk()
    app = EmailAttachmentDownloaderGUI(root)
    root.mainloop() 