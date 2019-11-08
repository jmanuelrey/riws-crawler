from goose3 import Goose
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider

import re, os, json

class TvTropesSpider(CrawlSpider):
	# Nombre del crawler
	name = 'tvtropes'
	# Dominios permitidos
	allowed_domains = ['tvtropes.org']
	# URLs iniciales
	start_urls = ['https://tvtropes.org/pmwiki/pagelist_having_pagetype_in_namespace.php?n=Main&t=trope&page=1']
	
	# Lista de medios
	media_list = ['Film', 'Series', 'Anime', 'Manga', 'VisualNovel', 'LightNovel', 'WesternAnimation', 'Disney', 'Animation', 'Toys', 'Literature', 'ComicBook', 'VideoGame', 'Website', 'Creator', 'Franchise', 'TabletopGame', 'Webcomic', 'Radio', 'Manhua', 'Manhwa', 'Music', 'Theatre', 'Myth', 'Ride'] # TODO rellenar
	
	# Reglas de crawling
	rules = (
		# Extraer enlaces de 'Main' y 'Laconic'
		Rule(
			LinkExtractor(
				allow=('pmwiki.php/Laconic')),
			callback='parse_item',
			follow=False),
		Rule(
			LinkExtractor(
				allow=('pmwiki.php/Main')),
			callback='parse_item',
			follow=True),
	)
	
	# Contadores
	iter_count = 0
	trope_count = 0
	laconic_count = 0
	non_trope_count = 0
	
	# Crawlear MAX_COUNT paginas
	# Nota: no se crawlean *exactamente* MAX_COUNT paginas
	MAX_COUNT = 10000
	custom_settings = {
			'CLOSESPIDER_PAGECOUNT': MAX_COUNT
	}
	
	# Obtener directorio actual
	current_directory = os.getcwd()
	# Obtener carpeta 'data' dentro del directorio
	final_directory = os.path.join(current_directory, 'data/')
	os.mkdir(final_directory)
	
	# Crear archivos asociados a un tropo, en formato json
	def create_files(self, json_file, file_name):
	
		# El nombre de la carpeta contenedora es de la forma 'titulo'-tropo o 'titulo'-laconic, 
		# con los espacios del titulo sustituidos por guiones
		file_dir = '{}-{}'.format(json_file['title'],file_name)
		file_dir = file_dir.replace(" ","-")
		# Crear jerarquia de carpetas
		# Para cada elemento, se crea una carpeta 'data/tropo' y otra 'data/laconic' (si tiene)
		# La carpeta 'data' solo se crea la primera vez
		if not os.path.exists(os.path.join(self.final_directory, file_dir + '/')):
			os.makedirs(self.final_directory + file_dir + '/')

		with open(self.final_directory + file_dir + '/' + file_name + '.json', 'w+', encoding='utf-8') as fp:
			json.dump(json_file, fp)
	
	# Generar objeto json con los datos del elemento
	def generate_json(self, article):
	
		title = article.title
		title = title.replace(' / Laconic', '') ###
		title = title.replace('/', '-') ###
		
		content = article.cleaned_text
		links = article.links
		current_url = article.canonical_link
		
		media_links = []
		non_media_links = []
		
		# Para cada enlace extraido por goose
		for(i, link) in enumerate(links):
			added = False
			# Para cada medio posible
			for media in self.media_list:
			# Si el enlace contiene uno de los medios, lo almacenamos en su lista
				if(re.search("\*/" + media + "/\*", link)):
					media_links.append(link)
					added = True
					break
			if(not added):
				# Si el enlace no contiene ningun medio, lo almacenamos en otra
				non_media_links.append(link)
		
		json_file = {
			"title": title,
			"content": content,
			"url": current_url,
			"media_links": media_links,
			"non_media_links": non_media_links,
		}
		
		return json_file
	
	# Parsear elemento
	def parse_item(self, response):
	
		self.iter_count += 1
		
		html = response.body
		
		# Objeto Goose para extraer datos de la pagina
		goose_extractor = Goose()
		article = goose_extractor.extract(raw_html=html)
		
		# Comprobar que la pagina contenga (por lo menos) un header h2 con la palabra 'Examples', para saber si es un tropo o no
		if(response.css('h2').re('.Examples.')):
			self.trope_count+=1
			follow = True
			json_file = self.generate_json(article)
			self.create_files(json_file, 'tropo')
			
			# Archivo para comprobar los tropos indexados
			with open(self.final_directory + 'trope_list.txt', 'a+', encoding='utf-8') as fp:
				fp.write(response.url+'\n')
			
		else:
			self.non_trope_count += 1
			if('Laconic' in response.url):
				print('Encontrado un Laconic!')
				self.laconic_count += 1
				json_file = self.generate_json(article)
				self.create_files(json_file, 'laconic')
			else:
				print('Enlace ignorado! (no era un tropo)')
			follow = False
		
		# Cerrar objeto goose
		goose_extractor.close()
		

	# Closed se llama cuando el spider termina de crawlear
	def closed(self, reason):
		self.logger.info('Closed spider: %s' % reason)
		self.logger.info('Total iterations: %s' % self.iter_count)
		self.logger.info('Trope count: %s' % self.trope_count)
		self.logger.info('Laconic count: %s' % self.laconic_count)
		self.logger.info('Non-trope count: %s' % self.non_trope_count)

''' Excepciones notables al formato habitual de tropo (no tienen ejemplos -> no es un tropo?):
Absurdism
AbsurdlyCoolCity
'''