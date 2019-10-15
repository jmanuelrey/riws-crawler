from goose3 import Goose
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider

import os, json

class TvTropesSpider(CrawlSpider):
	# Nombre del crawler
	name = 'tvtropes'
	# Dominios permitidos
	allowed_domains = ['tvtropes.org']
	# URLs iniciales
	start_urls = ['https://tvtropes.org/pmwiki/pagelist_having_pagetype_in_namespace.php?n=Main&t=trope&page=1']
	#start_urls = ['https://tvtropes.org/pmwiki/pmwiki.php/Main/TheManIsStickingItToTheMan']
	
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
	MAX_COUNT = 1000
	custom_settings = {
			'CLOSESPIDER_PAGECOUNT': MAX_COUNT
	}
	
	# Crear archivos asociados a un tropo, en formato json
	def create_files(self, json_file, file_name):
	
		# El nombre de la carpeta contenedora es de la forma 'titulo'-tropo o 'titulo'-laconic, 
		# con los espacios del titulo sustituidos por guiones
		file_dir = '{}-{}'.format(json_file['title'],file_name)
		file_dir = file_dir.replace(" ","-") 
	
		# Obtener directorio actual
		current_directory = os.getcwd()
		
		# Crear jerarquia de carpetas
		# Para cada elemento, se crea una carpeta 'data/tropo' y otra 'data/laconic' (si tiene)
		# La carpeta 'data' solo se crea la primera vez
		final_directory = os.path.join(current_directory, 'data/') # TODO: testear esta linea (y las siguientes) en Linux
		if not os.path.exists(os.path.join(final_directory, file_dir + '/')):
			os.makedirs(final_directory + file_dir + '/')

		with open(final_directory + file_dir + '/' + file_name + '.json', 'w+', encoding='utf-8') as fp:
			json.dump(json_file, fp)
	
	# Generar objeto json con los datos del elemento
	def generate_json(self, article):
	
		title = article.title
		content = article.cleaned_text
		links = article.links
		current_url = article.canonical_link
		
		json_file = {
			"title": title,
			"content": content,
			"url": current_url,
			"links": links
		}
		
		return json_file
	
	# Parsear elemento
	def parse_item(self, response):
	
		self.iter_count += 1
		
		html = response.body
		
		# Objeto Goose para extraer datos de la pagina
		goose_extractor = Goose()
		article = goose_extractor.extract(raw_html=html) # TODO: article parece que no contiene los enlaces Laconic. Corregir?
		
		# Comprobar que la pagina contenga (por lo menos) un header h2 con la palabra 'Examples', para saber si es un tropo o no
		if(response.css('h2').re('.Examples.')):
			self.trope_count+=1
			follow = True
			#json_file = self.generate_json(article)
			#self.create_files(json_file, 'tropo')
			
		else:
			self.non_trope_count += 1
			if('Laconic' in response.url):
				print('Encontrado un Laconic!')
				self.laconic_count += 1
				#json_file = self.generate_json(article)
				#self.create_files(json_file, 'laconic')
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