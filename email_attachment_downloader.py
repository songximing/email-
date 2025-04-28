import imaplib
import email
import os
from datetime import datetime
from dateutil import parser
from tqdm import tqdm
import getpass

class EmailAttachmentDownloader:
    def __init__(self, email_address, password, imap_server="imap.gmail.com", imap_port=993):
        """
        初始化邮件下载器
        :param email_address: 邮箱地址
        :param password: 邮箱密码或应用专用密码
        :param imap_server: IMAP服务器地址
        :param imap_port: IMAP服务器端口
        """
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.mail = None

    def connect(self):
        """连接到邮件服务器"""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mail.login(self.email_address, self.password)
            return True
        except Exception as e:
            print(f"连接失败: {str(e)}")
            return False

    def download_attachments(self, start_date, end_date, save_dir="attachments"):
        """
        下载指定时间段内的所有邮件附件
        :param start_date: 开始日期 (YYYY-MM-DD)
        :param end_date: 结束日期 (YYYY-MM-DD)
        :param save_dir: 附件保存目录
        """
        if not self.mail:
            print("未连接到邮件服务器")
            return

        # 创建保存目录
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # 选择收件箱
        self.mail.select('INBOX')

        # 构建搜索条件
        start = parser.parse(start_date).strftime("%d-%b-%Y")
        end = parser.parse(end_date).strftime("%d-%b-%Y")
        search_criteria = f'(SINCE "{start}" BEFORE "{end}")'
        
        # 搜索邮件
        try:
            _, message_numbers = self.mail.search(None, search_criteria)
        except Exception as e:
            print(f"搜索邮件失败: {str(e)}")
            return

        message_numbers = message_numbers[0].split()
        print(f"找到 {len(message_numbers)} 封邮件")

        # 遍历所有邮件
        for num in tqdm(message_numbers, desc="下载进度"):
            try:
                _, msg_data = self.mail.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                message = email.message_from_bytes(email_body)

                subject = self._decode_email_header(message.get('subject', 'No Subject'))
                date = message.get('date', 'No Date')

                # 处理附件
                for part in message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue

                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_email_header(filename)
                        # 使用日期和主题创建子文件夹
                        email_date = parser.parse(date).strftime("%Y%m%d")
                        subfolder = os.path.join(save_dir, email_date)
                        if not os.path.exists(subfolder):
                            os.makedirs(subfolder)

                        # 保存附件
                        filepath = os.path.join(subfolder, filename)
                        with open(filepath, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        print(f"\n已保存附件: {filepath}")

            except Exception as e:
                print(f"\n处理邮件时出错: {str(e)}")
                continue

    def _decode_email_header(self, header):
        """解码邮件头信息"""
        if header is None:
            return ""
        decoded_header = email.header.decode_header(header)
        return "".join([
            str(t[0], t[1] if t[1] else 'utf-8') if isinstance(t[0], bytes) else str(t[0])
            for t in decoded_header
        ])

    def close(self):
        """关闭连接"""
        if self.mail:
            self.mail.close()
            self.mail.logout()

def main():
    print("邮件附件下载器")
    print("-" * 50)
    
    # 获取用户输入
    email_address = input("请输入邮箱地址: ")
    password = getpass.getpass("请输入邮箱密码或应用专用密码: ")
    imap_server = input("请输入IMAP服务器地址 (默认 imap.gmail.com): ") or "imap.gmail.com"
    
    # 创建下载器实例
    downloader = EmailAttachmentDownloader(email_address, password, imap_server)
    
    if not downloader.connect():
        print("连接失败，程序退出")
        return

    # 获取日期范围
    start_date = input("请输入开始日期 (YYYY-MM-DD): ")
    end_date = input("请输入结束日期 (YYYY-MM-DD): ")
    save_dir = input("请输入保存目录 (默认 'attachments'): ") or "attachments"

    try:
        # 下载附件
        downloader.download_attachments(start_date, end_date, save_dir)
    finally:
        # 关闭连接
        downloader.close()

    print("\n下载完成！")

if __name__ == "__main__":
    main() 