from goose3 import Goose
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

import os, json

class TvTropesSpider(CrawlSpider):
	# Nombre del crawler
	name = 'tvtropes'
	# Dominios permitidos
	allowed_domains = ['tvtropes.org']
	# URLs iniciales
	start_urls = ['https://tvtropes.org/pmwiki/pagelist_having_pagetype_in_namespace.php?n=Main&t=trope&page=1']
	
	# Reglas de crawling
	rules = (
		# Extraer enlaces de 'Main' y 'Laconic'
		Rule(
			LinkExtractor(
				allow=('pmwiki.php/Main', 'pmwiki.php/Laconic')),
			callback='parse_item'),
	)
	
	# Contadores
	iter_count = 0
	trope_count = 0
	non_trope_count = 0
	
	# Crawlear MAX_COUNT paginas
	# Nota: no se crawlean *exactamente* MAX_COUNT paginas
	MAX_COUNT = 10
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
		final_directory = os.path.join(current_directory, 'data/') # Testear esta linea (y las siguientes) en Linux
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
		article = goose_extractor.extract(raw_html=html)
		
		# Comprobar que la pagina contenga (por lo menos) un header h2 con la palabra 'Examples', para saber si es un tropo o no
		if(response.css('h2').re('.Examples.')):
			self.trope_count+=1
			json_file = self.generate_json(article)
			self.create_files(json_file, 'tropo')
			
		else:
			self.non_trope_count += 1
			follow = False
			if('Laconic' in response.url):
				json_file = self.generate_json(article)
				self.create_files(json_file, 'laconic')
			
		# Cerrar objeto goose
		goose_extractor.close()
		

	# Closed se llama cuando el spider termina de crawlear
	def closed(self, reason):
		print('Total iterations: ', self.iter_count)
		print('Trope count: ', self.trope_count)
		print('Non-trope count: ', self.non_trope_count)
		self.logger.info('Closed spider: %s' % reason)
		
		

''' Excepciones notables al formato habitual de tropo (no tienen ejemplos -> no es un tropo?):
Absurdism
AbsurdlyCoolCity
'''