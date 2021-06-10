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
		'profile_gyfs_path': '[profile_path]/gyfs',
		'profile_photo_path': '[profile_path]/profile',
	}

	config_object['STORAGE'] = {
		'save_mp4': True,
		'save_mobile_mp4': False,
		'save_poster': True,
		'save_gyf_metadata': True,
		'save_single_gyfs_alone': False,
		'save_single_gyfs_with_user': True,
		'save_profile_along_with_gyf': True,
		'save_profile_photo': True,
		'save_profile_metadata': True,
		'mobile_mp4_file_name': '{gfyname}_mobile.{ext}',
		'mp4_file_name': '{gfyname}.{ext}',
		'poster_file_name': '[mp4_file_name]',
		'gyf_metadata_file_name': '{gfyname}.json',
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
	return str(round((size/1024000), 2)) +' MB'

def gyfMetadataRequest(gyf_name, stream = False):
	request = requests.get('https://api.redgifs.com/v1/gfycats/' + gyf_name, stream=stream)

	if request.ok:
		return request
	
	return None

def gyfRequest(url, stream = False):
	request = requests.get(url, stream=stream)

	if request.ok:
		return request

def populateTable(data, tree, window):
	count = 0
	tree.delete(*tree.get_children())
	tree['columns'] = ('id', 'section', 'name', 'size', 'status')
	tree.column('id', width='35')
	tree.heading('id', text='#', anchor='center')
	tree.column('name', width='300', anchor='center')
	tree.heading('name', text='Name')
	tree.column('section', width='300', anchor='center')
	tree.heading('section', text='Section')
	tree.column('size', width='120', anchor='center')
	tree.heading('size', text='File size')
	tree.column('status', width='140', anchor='center')
	tree.heading('status', text='Status')

	for x in data:
		section = None
		name = None

		if x.find('redgifs.com/') != -1:
			if x.find('/watch/') != -1:
				section = 'gyf'
				name = x.split('/watch/')
				name = ''.join([name[index] for index in [1]])
			else:
				section = 'gyf'
				name = x.split('.com/')
				name = ''.join([name[index] for index in [1]])

			if x.find('.webm') != -1 or x.find('.mp4') != -1:
				name = name.split('.')
				name = ''.join([name[index] for index in [0]])
		else:
			name = x

		if name:
			count += 1
			gyf_metadata = gyfMetadataRequest(name, True)

			if gyf_metadata:
				if 'gfyItem' in gyf_metadata.json() and 'mp4Url' in gyf_metadata.json()['gfyItem']:
					gyf_mp4 = gyfRequest(gyf_metadata.json()['gfyItem']['mp4Url'])
					total_length = int(gyf_mp4.headers.get('content-length'))
					tree.insert('', 'end', iid=count, values=(count, section, name, convertSize(total_length), 'Pending'))
					tree.yview(count-2)
					window.update()

def createPath(path):
	global env

	path_folders = path.split('/', 2)[-1].rsplit('/', 1)[0].split('/')

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

	request = request.json()['gfyItem'] if 'gfyItem' in request.json() else request.json()
	request = lower_keys(request)
	path = ''

	if section == 'gyf':
		if env['storage']['save_single_gyfs_alone'] == 'True' or (request['username'] == None or request['username'] == ''):
			path = env['route']['singles_path']
		
		if env['storage']['save_single_gyfs_with_user'] == 'True' or path == '':
			path = env['route']['profile_gyfs_path']
	elif section == 'user':
		if media_type == 'profile_photo':
			path = env['route']['profile_photo_path']
		elif media_type == 'profile_metadata':
			path = env['route']['profile_metadata_path']

	if media_type == 'mp4':
		path = path + '/' + env['storage']['mp4_file_name']

		dynamic_variables = re.findall(r"\{([A-Za-z0-9_]+)\}", path)

		if dynamic_variables != None:
			for group in dynamic_variables:
				if group != 'ext':
					path = path.replace('{' + group + '}', request[group])
				else:
					path = path.replace('{ext}', request['mp4url'].split('.')[-1])

		createPath(path)
	elif media_type == 'mobile_mp4':
		path = path + '/' + env['storage']['mobile_mp4_file_name']

		dynamic_variables = re.findall(r"\{([A-Za-z0-9_]+)\}", path)

		if dynamic_variables != None:
			for group in dynamic_variables:
				if group != 'ext':
					path = path.replace('{' + group + '}', request[group])
				else:
					path = path.replace('{ext}', request['mobileurl'].split('.')[-1])
		
		createPath(path)
	elif media_type == 'poster':
		path = path + '/' + env['storage']['poster_file_name']

		dynamic_variables = re.findall(r"\{([A-Za-z0-9_]+)\}", path)

		if dynamic_variables != None:
			for group in dynamic_variables:
				if group != 'ext':
					path = path.replace('{' + group + '}', request[group])
				else:
					path = path.replace('{ext}', request['posterurl'].split('.')[-1])
		
		createPath(path)
	elif media_type == 'gyf_metadata':
		path = path + '/' + env['storage']['gyf_metadata_file_name']

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
		global data, data2

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
						section = 'gyf'
						name = x.split('/watch/')
						name = ''.join([name[index] for index in [1]])
					else:
						section = 'gyf'
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

				if name:
					gyf_metadata = gyfMetadataRequest(name, True)

					if gyf_metadata:
						if env['storage']['save_mp4'] == 'True':
							if 'gfyItem' in gyf_metadata.json() and 'mp4Url' in gyf_metadata.json()['gfyItem']:
								gyf_mp4 = gyfRequest(gyf_metadata.json()['gfyItem']['mp4Url'], True)
								total_length = int(gyf_mp4.headers.get('content-length'))
								tree.item(count, values=(count, section + ' - mp4', name, convertSize(total_length), 'Downloading'))
								tree.yview(count-1)
								window.update()

							gyf_mp4_path = formatFilePath(gyf_metadata, 'mp4', section)

							if not os.path.exists(gyf_mp4_path) or (os.path.exists(gyf_mp4_path) and os.path.getsize(gyf_mp4_path) <= 0):
								with open(gyf_mp4_path, 'wb') as f:
									bar['maximum'] = total_length

									for chunk in gyf_mp4.iter_content(chunk_size=1024):
										if chunk:
											bar.step(1024)
											window.update()
											f.write(chunk)
											f.flush()
						
						if env['storage']['save_mobile_mp4'] == 'True':
							if 'gfyItem' in gyf_metadata.json() and 'mobileUrl' in gyf_metadata.json()['gfyItem']:
								gyf_mobile_mp4 = gyfRequest(gyf_metadata.json()['gfyItem']['mobileUrl'], True)
								total_length = int(gyf_mobile_mp4.headers.get('content-length'))
								tree.item(count, values=(count, section + ' - mobile mp4', name, convertSize(total_length), 'Downloading'))
								tree.yview(count-1)
								window.update()

							gyf_mobile_mp4_path = formatFilePath(gyf_metadata, 'mobile_mp4', section)

							if not os.path.exists(gyf_mobile_mp4_path) or (os.path.exists(gyf_mobile_mp4_path) and os.path.getsize(gyf_mobile_mp4_path) <= 0):
								with open(gyf_mobile_mp4_path, 'wb') as f:
									bar['maximum'] = total_length

									for chunk in gyf_mobile_mp4.iter_content(chunk_size=1024):
										if chunk:
											bar.step(1024)
											window.update()
											f.write(chunk)
											f.flush()
						
						if env['storage']['save_poster'] == 'True':
							if 'gfyItem' in gyf_metadata.json() and 'posterUrl' in gyf_metadata.json()['gfyItem']:
								gyf_poster = gyfRequest(gyf_metadata.json()['gfyItem']['posterUrl'], True)
								total_length = int(gyf_poster.headers.get('content-length'))
								tree.item(count, values=(count, section + ' - poster', name, convertSize(total_length), 'Downloading'))
								tree.yview(count-1)
								window.update()

							gyf_poster_path = formatFilePath(gyf_metadata, 'poster', section)

							if not os.path.exists(gyf_poster_path) or (os.path.exists(gyf_poster_path) and os.path.getsize(gyf_poster_path) <= 0):
								with open(gyf_poster_path, 'wb') as f:
									bar['maximum'] = total_length

									for chunk in gyf_poster.iter_content(chunk_size=1024):
										if chunk:
											bar.step(1024)
											window.update()
											f.write(chunk)
											f.flush()
						
						if env['storage']['save_gyf_metadata'] == 'True':
							total_length = int(gyf_metadata.headers.get('content-length'))
							tree.item(count, values=(count, section + ' - metadata', name, convertSize(total_length), 'Downloading'))
							tree.yview(count-1)
							window.update()

							gyf_metadata_path = formatFilePath(gyf_metadata, 'gyf_metadata', section)

							if not os.path.exists(gyf_metadata_path) or (os.path.exists(gyf_metadata_path) and os.path.getsize(gyf_metadata_path) <= 0):
								with open(gyf_metadata_path, 'w') as f:
									bar['maximum'] = 100
									bar['value'] = 100
									f.write(json.dumps(gyf_metadata.json(), indent=4, sort_keys=True))
									f.flush()
									window.update()
				
						if env['storage']['save_profile_along_with_gyf'] == 'True':
							user_request = requests.get('https://api.redgifs.com/v1/users/' + gyf_metadata.json()['gfyItem']['userName'])

							if user_request.ok:
								if env['storage']['save_profile_photo'] == 'True' and 'profileImageUrl' in user_request.json():
									profile_photo = gyfRequest(user_request.json()['profileImageUrl'], True)
									total_length = int(profile_photo.headers.get('content-length'))
									tree.item(count, values=(count, section + ' - profile photo', name, convertSize(total_length), 'Downloading'))
									tree.yview(count-1)
									window.update()
									profile_photo_path = formatFilePath(user_request, 'profile_photo', 'user')

									if not os.path.exists(profile_photo_path) or (os.path.exists(profile_photo_path) and os.path.getsize(profile_photo_path) <= 0):
										with open(profile_photo_path, 'w') as f:
											bar['maximum'] = total_length

											for chunk in profile_photo.iter_content(chunk_size=1024):
												if chunk:
													bar.step(1024)
													window.update()
													f.write(chunk)
													f.flush()

								if env['storage']['save_profile_metadata'] == 'True':
									total_length = int(user_request.headers.get('content-length'))
									tree.item(count, values=(count, section + ' - profile metadata', name, convertSize(total_length), 'Downloading'))
									tree.yview(count-1)
									window.update()

									profile_metadata_path = formatFilePath(user_request, 'profile_metadata', 'user')

									if not os.path.exists(profile_metadata_path) or (os.path.exists(profile_metadata_path) and os.path.getsize(profile_metadata_path) <= 0):
										with open(profile_metadata_path, 'w') as f:
											bar['maximum'] = 100
											bar['value'] = 100
											f.write(json.dumps(user_request.json(), indent=4, sort_keys=True))
											f.flush()
											window.update()

				tree.item(count, values=(count, section, name, convertSize(total_length), 'Completed'))

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
