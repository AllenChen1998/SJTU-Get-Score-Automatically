from selenium import webdriver
from prettytable import PrettyTable
import smtplib    
from email.mime.multipart import MIMEMultipart    
from email.mime.text import MIMEText    
from email.header import Header   

import cv2
import os
import time
import re
import csv
import numpy as np


def get_saved_source():
	with open("test.txt", 'r', encoding='utf-8') as f:
		txt = f.read()
	return txt


def get_browser():
	cache_path = "D:\\cache.png"
	option = webdriver.ChromeOptions()
	option.add_argument('--headless')
	browser = webdriver.Chrome(chrome_options=option)

	browser.get("http://wechat.shwilling.com/sjtu/exam/pub/Fqqa")
	button = browser.find_element_by_class_name('btm-center')
	button.click()
	browser.get_screenshot_as_file(cache_path)

	qr = cv2.imread(cache_path)
	cv2.imshow("Login QR Code", qr)
	cv2.waitKey(0)
	cv2.destroyAllWindows()
	os.remove(cache_path)

	browser.get("http://wechat.shwilling.com/sjtu/exam/pub/Fqqa")
	return browser


def get_credit():
	credit = {}
	for i, item in enumerate(csv.reader(open("credit.csv", 'r'))):
		if not i: continue
		credit[item[0]] = float(item[1])
	return credit


def cal_gpa(score, credit):
	if score >= 95:   return credit * 4.3
	elif score >= 90: return credit * 4.0
	elif score >= 85: return credit * 3.7
	elif score >= 80: return credit * 3.3
	elif score >= 75: return credit * 3.0
	elif score >= 70: return credit * 2.7
	elif score >= 67: return credit * 2.3
	elif score >= 65: return credit * 2.0
	elif score >= 62: return credit * 1.7
	elif score >= 60: return credit * 1.0


def parse_html(html, credit):
	cla = re.findall(r'<div class="">(.*?)</div>', html, re.S)
	score = re.findall(r'i-d-remain">(.*?)</div>', html, re.S)
	rank = re.findall(r'排名<br>(.*?)</div>', html, re.S)
	total = re.findall(r'总人数<br>(.*?)</div>', html, re.S)
	average = re.findall(r'平均分<br> (.*?)</div>', html, re.S)
	highest = re.findall(r'最高分<br>(.*?)</div>', html, re.S)
	if len(cla) == 0: return None, '', 0, 0, 0

	total_point = 0
	total_score = 0
	sum_credit = 0
	interval = '     '
	output = ''
	table = PrettyTable(["Class", "Score", "Average", "Highest", "Rank"])
	table.align["Class"] = "l"
	
	for i in range(len(cla)):
		sum_credit += credit[cla[i]]
		total_point += cal_gpa(float(score[i]), credit[cla[i]])
		total_score += credit[cla[i]] * float(score[i])
		table.add_row([cla[i], score[i], average[i], highest[i], rank[i] + '/' + total[i]])
		output += cla[i] + interval + score[i] + '/' + average[i] + '/' + highest[i] + interval + rank[i] + '/' + total[i] + '\n'
	
	gpa = round(total_point/sum_credit, 4)
	ave_score = round(total_score/sum_credit, 4)
	text = 'GPA  ' + str(gpa) + interval + '学积分  ' + str(ave_score) + '\n'
	text += '课程' + interval + '成绩/平均分/最高分' + interval + '名次/总人数' + '\n' + output
	return table, text, len(cla), gpa, ave_score


def send_email(text, smtp, sender, password, receiver):
	msg = MIMEMultipart('mixed') 
	msg['Subject'] = Header('您有新的成绩待查收', 'utf-8').encode()
	msg['From'] = sender
	msg['To'] = receiver
   
	text_plain = MIMEText(text, 'plain', 'gb2312')    
	msg.attach(text_plain)    
	smtp.sendmail(sender, receiver, msg.as_string())    
	

def get_score_constantly(sender='allenchencsz@163.com', password='getyourscore123', receiver='729020210@qq.com', time_interval=30):
	browser = get_browser()
	credit = get_credit()
	start = time.time()

	smtp = smtplib.SMTP()    
	smtp.connect('smtp.163.com')
	smtp.login(sender, password)
	avaliable = 0
	while 1:
		try:
			table, text, current_avaliable, gpa, ave_score = parse_html(browser.page_source, credit) #parse_html(get_saved_source())
			print("\n[ Score", ave_score, "] [ GPA", gpa, '] [ Class', avaliable, "] [ Time", round(time.time()-start), ']\n')
			time.sleep(time_interval)
			if not current_avaliable: continue
			if current_avaliable > avaliable:
				print("\nDetected new score! Email sended to " + receiver + '!')
				print(table, '\n')
				send_email(text, smtp, sender, password, receiver)
			refresh_button = browser.find_element_by_class_name('btm-left')
			refresh_button.click()
			avaliable = current_avaliable
		except KeyboardInterrupt:
			smtp.quit()


if __name__ == "__main__":
	get_score_constantly()