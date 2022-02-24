import os
import re
import pygubu
import configparser
import requests
import json
from configparser import ConfigParser
from tkinter import messagebox
from tkinter import filedialog

PROJECT_PATH = os.path.dirname(__file__)
PROJECT_UI = os.path.join(PROJECT_PATH, 'windows.ui')
env = {}
folder = 0
data = 0

def configLoader():
	global folder, env

	config_object = ConfigParser()
	config_object.read('cfg.ini')
	route = config_object['ROUTE']
	folder = route['root_directory']

	for section in config_object.sections():
		section_params = {}

		for item in config_object.items(section):
			config_key = item[0]
			config_value = item[1]

			config_param_groups = re.findall(r"\[([A-Za-z0-9_]+)\]", config_value)

			if config_param_groups != None:
				for group in config_param_groups:
					config_value = config_value.replace('[' + group + ']', (section_params[config_key] if config_key in section_params else config_object[section].get(group)))

					config_param_groups = re.findall(r"\[([A-Za-z0-9_]+)\]", config_value)

					if config_param_groups != None:
						for group in config_param_groups:
							config_value = config_value.replace('[' + group + ']', (section_params[config_key] if config_key in section_params else config_object[section].get(group)))

			section_params[config_key] = config_value
		
		env[section.lower()] = section_params

def configCreator():
	config_object = ConfigParser()
	config_object['ROUTE'] = {
		'root_directory': folder,
		'profile_path': '[root_directory]/profiles/{username}',
		'singles_path': '[root_directory]singles',
		'profile_metadata_path': '[profile_path]/metadata',
		'profile_gifs_path': '[profile_path]/gifs',
		'profile_images_path': '[profile_path]/images',
		'profile_photo_path': '[profile_path]/profile',
	}

	config_object['STORAGE'] = {
		'save_mp4': True,
		'save_mobile_mp4': False,
		'save_poster': True,
		'save_gif_metadata': True,
		'save_single_gifs_alone': False,
		'save_single_gifs_with_user': True,
		'save_profile_along_with_gif': True,
		'save_profile_photo': True,
		'save_profile_metadata': True,
		'mobile_mp4_file_name': '{id}_mobile.{ext}',
		'mp4_file_name': '{id}.{ext}',
		'poster_file_name': '[mp4_file_name]',
		'gif_metadata_file_name': '{id}.json',
		'profile_photo_file_name': '{username}.{ext}',
		'profile_metadata_file_name': '{username}.json',
	}

	with open(PROJECT_PATH + '/cfg.ini', 'w') as config:
		config_object.write(config)

def configRewrite(folder):
	global env

	config_object = ConfigParser()
	config_object.read('cfg.ini')
	route = config_object['ROUTE']
	route['root_directory'] = folder

	env['route']['root_directory'] = folder

	with open(PROJECT_PATH + '/cfg.ini', 'w') as config:
		config_object.write(config)

def convertSize(size):
	return str(round((size/1024000), 2)) + ' MB'

def gifMetadataRequest(gif_name, stream = False):
	request = requests.get('https://api.redgifs.com/v2/gifs/' + gif_name, stream=stream)

	if request.ok:
		return request
	
	return None

def userMetadataRequest(username, stream = False):
	request = requests.get('https://api.redgifs.com/v1/users/' + username, stream=stream)

	if request.ok:
		return request
	
	return None

def gifRequest(url, stream = False):
	request = requests.get(url, stream=stream)

	if request.ok:
		return request

def populateTable(data, tree, window):
	count = 0
	tree.delete(*tree.get_children())
	tree['columns'] = ('id', 'section', 'name', 'status')
	tree.column('id', width='35')
	tree.heading('id', text='#', anchor='center')
	tree.column('name', width='300', anchor='center')
	tree.heading('name', text='Name')
	tree.column('section', width='300', anchor='center')
	tree.heading('section', text='Section')
	tree.column('status', width='140', anchor='center')
	tree.heading('status', text='Status')

	for x in data:
		section = None
		name = None

		if x.find('redgifs.com/') != -1:
			if x.find('/watch/') != -1:
				section = 'gif'
				name = x.split('/watch/')
				name = ''.join([name[index] for index in [1]])
			elif x.find('/users/') != -1:
				section = 'user'
				name = x.split('/users/')
				name = ''.join([name[index] for index in [1]])
			else:
				section = 'gif'
				name = x.split('.com/')
				name = ''.join([name[index] for index in [1]])

			if x.find('.webm') != -1 or x.find('.mp4') != -1:
				name = name.split('.')
				name = ''.join([name[index] for index in [0]])
		else:
			name = x

		if name:
			count += 1
			
			tree.insert('', 'end', iid=count, values=(count, section, name, 'Pending'))
			tree.yview(count-2)
			window.update()

def createPath(path):
	global env

	path_folders = path.replace(env['route']['root_directory'], '').split('/', 1)[-1].rsplit('/', 1)[0].split('/')

	current_path_pointer = env['route']['root_directory']

	for folder in path_folders:
		if not os.path.exists(current_path_pointer + '/' +  folder):
			os.mkdir(current_path_pointer + '/' +  folder)

		current_path_pointer = current_path_pointer + '/' +  folder

def lower_keys(x):
	if isinstance(x, list):
		return [lower_keys(v) for v in x]
	elif isinstance(x, dict):
		return dict((k.lower(), lower_keys(v)) for k, v in x.items())
	else:
		return x

def formatFilePath(request, media_type, section):
	global env

	request = request['gfyItem'] if 'gfyItem' in request else request
	request = lower_keys(request)
	path = ''

	if section == 'gif':
		if env['storage']['save_single_gifs_alone'] == 'True' or (request['username'] == None or request['username'] == ''):
			path = env['route']['singles_path']
		
		if env['storage']['save_single_gifs_with_user'] == 'True' or path == '':
			path = env['route']['profile_gifs_path']
	elif section == 'user':
		if media_type == 'profile_photo':
			path = env['route']['profile_photo_path']
		elif media_type == 'profile_metadata':
			path = env['route']['profile_metadata_path']
		else:
			path = env['route']['profile_gifs_path']

	if media_type == 'mp4':
		path = path + '/' + env['storage']['mp4_file_name']

		dynamic_variables = re.findall(r"\{([A-Za-z0-9_]+)\}", path)

		if dynamic_variables != None:
			for group in dynamic_variables:
				if group != 'ext':
					path = path.replace('{' + group + '}', request[group])
				else:
					path = path.replace('{ext}', request['urls']['hd'].split('.')[-1])

		createPath(path)
	elif media_type == 'mobile_mp4':
		path = path + '/' + env['storage']['mobile_mp4_file_name']

		dynamic_variables = re.findall(r"\{([A-Za-z0-9_]+)\}", path)

		if dynamic_variables != None:
			for group in dynamic_variables:
				if group != 'ext':
					path = path.replace('{' + group + '}', request[group])
				else:
					path = path.replace('{ext}', request['urls']['sd'].split('.')[-1])
		
		createPath(path)
	elif media_type == 'poster':
		path = path + '/' + env['storage']['poster_file_name']

		dynamic_variables = re.findall(r"\{([A-Za-z0-9_]+)\}", path)

		if dynamic_variables != None:
			for group in dynamic_variables:
				if group != 'ext':
					path = path.replace('{' + group + '}', request[group])
				else:
					path = path.replace('{ext}', request['urls']['poster'].split('.')[-1])
		
		createPath(path)
	elif media_type == 'gif_metadata':
		path = path + '/' + env['storage']['gif_metadata_file_name']

		dynamic_variables = re.findall(r"\{([A-Za-z0-9_]+)\}", path)

		if dynamic_variables != None:
			for group in dynamic_variables:
				if group != 'ext':
					path = path.replace('{' + group + '}', request[group])

		createPath(path)
	elif media_type == 'profile_photo':
		path = path + '/' + env['storage']['profile_photo_file_name']

		dynamic_variables = re.findall(r"\{([A-Za-z0-9_]+)\}", path)

		if dynamic_variables != None:
			for group in dynamic_variables:
				if group != 'ext':
					path = path.replace('{' + group + '}', request[group])
				else:
					path = path.replace('{ext}', request['profileimageurl'].split('.')[-1])

		createPath(path)
	elif media_type == 'profile_metadata':
		path = path + '/' + env['storage']['profile_metadata_file_name']

		dynamic_variables = re.findall(r"\{([A-Za-z0-9_]+)\}", path)

		if dynamic_variables != None:
			for group in dynamic_variables:
				if group != 'ext':
					path = path.replace('{' + group + '}', request[group])

		createPath(path)

	return path

def getUserGifs(username, page = 1):
	user_gifs = []

	user_gifs_request = requests.get('https://api.redgifs.com/v2/users/' + username + '/search?order=recent&type=g&page=' + str(page))

	if user_gifs_request.ok:
		user_gifs = user_gifs_request.json()['gifs']

		if page < int(user_gifs_request.json()['pages']):
			user_gifs = user_gifs + getUserGifs(username, (int(user_gifs_request.json()['page']) + 1))
		
	return user_gifs

def downloadGif(gif_request, name, section, total_length, count, window, tree, bar, pretty_name):
	global env
	
	gif_metadata = gif_request.json() if type(gif_request) != dict else gif_request
	gif_metadata = gif_metadata['gif'] if 'gif' in gif_metadata else gif_metadata

	if env['storage']['save_mp4'] == 'True':
		if ('urls' in gif_metadata and 'hd' in gif_metadata['urls']) or ('hd' in gif_metadata):
			hd_Url = gif_metadata['urls']['hd'] if ('urls' in gif_metadata and 'hd' in gif_metadata['urls']) else gif_metadata['hd']
			gif_mp4 = gifRequest(hd_Url, True)

			if gif_mp4 != None and gif_mp4.ok:
				total_length = int(gif_mp4.headers.get('Content-Length')) if 'Content-Length' in gif_mp4.headers else 0
				tree.item(count, values=(count, pretty_name + ' - mp4', name, 'Downloading'))
				tree.yview(count-1)
				window.update()

				gif_mp4_path = formatFilePath(gif_metadata, 'mp4', section)

				if not os.path.exists(gif_mp4_path) or (os.path.exists(gif_mp4_path) and os.path.getsize(gif_mp4_path) <= 0):
					with open(gif_mp4_path, 'wb') as f:
						bar['maximum'] = total_length

						for chunk in gif_mp4.iter_content(chunk_size=1024):
							if chunk:
								bar.step(1024)
								window.update()
								f.write(chunk)
								f.flush()
	
	if env['storage']['save_mobile_mp4'] == 'True':
		if ('urls' in gif_metadata and 'sd' in gif_metadata['urls']) or ('sd' in gif_metadata):
			sd_Url = gif_metadata['urls']['sd'] if ('urls' in gif_metadata and 'sd' in gif_metadata['urls']) else gif_metadata['sd']
			gif_mobile_mp4 = gifRequest(sd_Url, True)

			if gif_mobile_mp4 != None and gif_mobile_mp4.ok:
				total_length = int(gif_mobile_mp4.headers.get('Content-Length')) if 'Content-Length' in gif_mobile_mp4.headers else 0
				tree.item(count, values=(count, pretty_name + ' - mobile mp4', name, 'Downloading'))
				tree.yview(count-1)
				window.update()

				gif_mobile_mp4_path = formatFilePath(gif_metadata, 'mobile_mp4', section)

				if not os.path.exists(gif_mobile_mp4_path) or (os.path.exists(gif_mobile_mp4_path) and os.path.getsize(gif_mobile_mp4_path) <= 0):
					with open(gif_mobile_mp4_path, 'wb') as f:
						bar['maximum'] = total_length

						for chunk in gif_mobile_mp4.iter_content(chunk_size=1024):
							if chunk:
								bar.step(1024)
								window.update()
								f.write(chunk)
								f.flush()
	
	if env['storage']['save_poster'] == 'True':
		if ('urls' in gif_metadata and 'poster' in gif_metadata['urls']) or ('poster' in gif_metadata):
			poster_Url = gif_metadata['urls']['poster'] if ('urls' in gif_metadata and 'poster' in gif_metadata['urls']) else gif_metadata['poster']
			gif_poster = gifRequest(poster_Url, True)

			if gif_poster != None and gif_poster.ok:
				total_length = int(gif_poster.headers.get('Content-Length')) if 'Content-Length' in gif_poster.headers else 0
				tree.item(count, values=(count, pretty_name + ' - poster', name, 'Downloading'))
				tree.yview(count-1)
				window.update()

				gif_poster_path = formatFilePath(gif_metadata, 'poster', section)

				if not os.path.exists(gif_poster_path) or (os.path.exists(gif_poster_path) and os.path.getsize(gif_poster_path) <= 0):
					with open(gif_poster_path, 'wb') as f:
						bar['maximum'] = total_length

						for chunk in gif_poster.iter_content(chunk_size=1024):
							if chunk:
								bar.step(1024)
								window.update()
								f.write(chunk)
								f.flush()
	
	if env['storage']['save_gif_metadata'] == 'True':
		total_length = 0
		tree.item(count, values=(count, pretty_name + ' - metadata', name, 'Downloading'))
		tree.yview(count-1)
		window.update()

		gif_metadata_path = formatFilePath(gif_metadata, 'gif_metadata', section)

		if not os.path.exists(gif_metadata_path) or (os.path.exists(gif_metadata_path) and os.path.getsize(gif_metadata_path) <= 0):
			with open(gif_metadata_path, 'w') as f:
				bar['maximum'] = 100
				bar['value'] = 100
				f.write(json.dumps(gif_metadata, indent=4, sort_keys=True))
				f.flush()
				window.update()

	if section == 'gif' and env['storage']['save_profile_along_with_gif'] == 'True':
		user_request_raw = userMetadataRequest(gif_metadata['userName'])

		if user_request_raw.ok:
			user_request = user_request_raw.json()

			if env['storage']['save_profile_photo'] == 'True' and 'profileImageUrl' in user_request and not user_request['profileImageUrl'] == None:
				profile_photo = gifRequest(user_request['profileImageUrl'], True)
				total_length = int(profile_photo.headers.get('Content-Length')) if 'Content-Length' in profile_photo.headers else 0
				tree.item(count, values=(count, pretty_name + ' - profile photo', name, 'Downloading'))
				tree.yview(count-1)
				window.update()
				profile_photo_path = formatFilePath(user_request, 'profile_photo', 'user')

				if not os.path.exists(profile_photo_path) or (os.path.exists(profile_photo_path) and os.path.getsize(profile_photo_path) <= 0):
					with open(profile_photo_path, 'wb') as f:
						bar['maximum'] = total_length

						for chunk in profile_photo.iter_content(chunk_size=1024):
							if chunk:
								bar.step(1024)
								window.update()
								f.write(chunk)
								f.flush()

			if env['storage']['save_profile_metadata'] == 'True':
				total_length = int(user_request_raw.headers.get('Content-Length')) if 'Content-Length' in user_request_raw.headers else 0
				tree.item(count, values=(count, pretty_name + ' - profile metadata', name, 'Downloading'))
				tree.yview(count-1)
				window.update()

				profile_metadata_path = formatFilePath(user_request, 'profile_metadata', 'user')

				if not os.path.exists(profile_metadata_path) or (os.path.exists(profile_metadata_path) and os.path.getsize(profile_metadata_path) <= 0):
					with open(profile_metadata_path, 'w') as f:
						bar['maximum'] = 100
						bar['value'] = 100
						f.write(json.dumps(user_request, indent=4, sort_keys=True))
						f.flush()
						window.update()

class RedGifsDownloader:
	def __init__(self):
		self.builder = builder = pygubu.Builder()
		builder.add_resource_path(PROJECT_PATH)
		builder.add_from_file(PROJECT_UI)
		self.mainwindow = builder.get_object('toplevel')
		builder.connect_callbacks(self)

		if os.path.isfile(PROJECT_PATH + '/cfg.ini'):
			configLoader()
			text = builder.get_variable('lbl_foldervar')			
			text.set('Current folder: ' + (folder if folder != '0' else 'none'))
		else:
			configCreator()
		
	def getDirectory(self):
		global folder

		folder = filedialog.askdirectory()

		if folder != '':
			text = self.builder.get_variable('lbl_foldervar')
			text.set('Current file: ' + folder)
			configRewrite(folder)

	def openFile(self):
		global data, data2, folder

		filename = filedialog.askopenfilename(filetypes=[('Text files', '*.txt')])

		if filename != '':
			text = self.builder.get_variable('lbl_filevar')
			text.set('Current file: ' + filename)

			with open (filename, 'r') as myfile:
				data = myfile.read().split('\n')

			data2 = data
			populateTable(data, self.builder.get_object('tv_files'), self.builder.get_object('toplevel'))

	def downloadFiles(self):
		global data, data2, folder, env

		count = 0
		window = self.builder.get_object('toplevel')
		tree = self.builder.get_object('tv_files')

		if data != 0 and folder != 0:
			bar = self.builder.get_object('pb_download')

			for x in data:
				section = None
				name = None

				if x.find('redgifs.com/') != -1:
					if x.find('/watch/') != -1:
						section = 'gif'
						name = x.split('/watch/')
						name = ''.join([name[index] for index in [1]])
					elif x.find('/users/') != -1:
						section = 'user'
						name = x.split('/users/')
						name = ''.join([name[index] for index in [1]])
					else:
						section = 'gif'
						name = x.split('.com/')
						name = ''.join([name[index] for index in [1]])

					if x.find('.webm') != -1 or x.find('.mp4') != -1:
						name = name.split('.')
						name = ''.join([name[index] for index in [0]])
				else:
					name = x

				total_length = 0
				bar['value'] = 0
				count += 1

				if name and section == 'gif':
					gif_metadata = gifMetadataRequest(name, True)

					if gif_metadata and gif_metadata.ok:
						downloadGif(gif_metadata, name, section, total_length, count, window, tree, bar, pretty_name=section)
				elif name and section == 'user':
					user_metadata = userMetadataRequest(name, True)

					if user_metadata:				
						if env['storage']['save_profile_photo'] == 'True' and 'profileImageUrl' in user_metadata.json() and not user_metadata.json()['profileImageUrl'] == None:
							profile_photo = gifRequest(user_metadata.json()['profileImageUrl'], True)
							total_length = int(profile_photo.headers.get('Content-Length')) if 'Content-Length' in profile_photo.headers else 0
							tree.item(count, values=(count, section + ' - profile photo', name, 'Downloading'))
							tree.yview(count-1)
							window.update()

							profile_photo_path = formatFilePath(user_metadata.json(), 'profile_photo', 'user')

							if not os.path.exists(profile_photo_path) or (os.path.exists(profile_photo_path) and os.path.getsize(profile_photo_path) <= 0):
								with open(profile_photo_path, 'wb') as f:
									bar['maximum'] = total_length

									for chunk in profile_photo.iter_content(chunk_size=1024):
										if chunk:
											bar.step(1024)
											window.update()
											f.write(chunk)
											f.flush()

						if env['storage']['save_profile_metadata'] == 'True':
							total_length = int(user_metadata.headers.get('Content-Length')) if 'Content-Length' in user_metadata.headers else 0
							tree.item(count, values=(count, section + ' - profile metadata', name, 'Downloading'))
							tree.yview(count-1)
							window.update()

							profile_metadata_path = formatFilePath(user_metadata.json(), 'profile_metadata', 'user')

							if not os.path.exists(profile_metadata_path) or (os.path.exists(profile_metadata_path) and os.path.getsize(profile_metadata_path) <= 0):
								with open(profile_metadata_path, 'w') as f:
									bar['maximum'] = 100
									bar['value'] = 100
									f.write(json.dumps(user_metadata.json(), indent=4, sort_keys=True))
									f.flush()
									window.update()

					user_gifs = getUserGifs(name)
					user_pointer = 1

					for gif in user_gifs:
						downloadGif(gif, name, section, total_length, count, window, tree, bar, pretty_name=(section + ' - ' + str(user_pointer) + '/' + str(len(user_gifs))))

						user_pointer += 1

				tree.item(count, values=(count, section, name, 'Completed'))

			bar['maximum'] = 100
			bar['value'] = 100
			messagebox.showinfo('RedGifs Downloader', 'Finished')
			data = data2
		else:
			if data == 0 and folder != 0:
				messagebox.showinfo('RedGifs Downloader', 'Please select a file with the names')
			elif data != 0 and folder == 0:
				messagebox.showinfo('RedGifs Downloader', 'Please select a folder')
			else:
				messagebox.showinfo('RedGifs Downloader', 'Please select a file with the names and a folder')

	def run(self):
		self.mainwindow.mainloop()

if __name__ == '__main__':
	app = RedGifsDownloader()
	app.run()
