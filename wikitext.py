#!/usr/bin/python3
# Functions for cleaning up a wiki entry so it's more readable
# Unlike the rest of wordtree, I finally got with the times and vibe coded most of this.

import re
import html


from letters import eprint
from languages import LANGCODES

# 2do fix entries for: fastuoso

TEMPLATE_REPLACEMENTS = {
	"unc": "Uncertain",
	"syn": "Synonym",
	"alt": "Alternative form",
	"ant": "Antonym",
	"abbr": "Abbreviation",
	"con": "Contraction",
	"var": "Variant",
	"nonstandard": "Nonstandard",
	"colloquial": "Colloquial",
	"archaic": "Archaic",
	"rare": "Rare",
	"obs": "Obsolete",
	"proscribed": "Proscribed",
	"misspelling": "Misspelling",
	"slang": "Slang",
	"diminutive": "Diminutive",
	"pejorative": "Pejorative",
	"euphemistic": "Euphemistic",
	"humorous": "Humorous",
	"informal": "Informal",
	"derogatory": "Derogatory",
	"vulgar": "Vulgar",
	"eye dialect": "Eye dialect",
	"only used in": "Only used in",
}

IGNORE_TEMPLATES = {
	"was fwotd", "attention", "rfc", "rft", "rfe", "pedia", "Wikipedia",
	"wikipedia-sister", "commonscat", "checktrans-top", "checktrans-mid",
	"checktrans-bottom", "t-check", "t-needed", "tea room", "shortcut",
	"noinclude", "onlyinclude", "includeonly", "qualifier needed", "merge",
	"delete", "speedy deletion", "editprotected", "vote", "votepl",
	"support", "oppose", "WOTD", "FWOTD", "COTD"
}




#######################################################
# Functions


def parse_noun_template(template):
	# print('parse noun', template)
	match = re.match(r"\{\{([a-z]{2})-noun\|([^{}]+)\}\}", template)
	if not match:
		return template  # return unchanged if it doesn't match

	_, args_str = match.groups()		# _ is lang
	args = args_str.split('|')

	# First argument is usually gender
	gender = args[0]
	options = {k: v for a in args[1:] if '=' in a for k, v in [a.split('=', 1)]}

	gender_map = {
		'm': 'masculine noun',
		'f': 'feminine noun',
		'm-p': 'masculine plural noun',
		'f-p': 'feminine plural noun',
	}

	description = gender_map.get(gender, f"{gender} noun")

	if options.get('f') == '+':
		description += " (additional feminine form)"

	return description


def preserve_glosses(wikitext):
	# Extract values of t=, gloss=, lit= and replace with just their values
	wikitext = re.sub(r'\|\s*(t|gloss|lit)\s*=\s*([^|}]+)', r' (\2)', wikitext)
	# Remove unwanted parameters entirely
	wikitext = re.sub(r'\|\s*(g|id|tr|ts|sc|nocap|notr|noe|nopal|pos|lang|alt)\s*=\s*[^|}]+', '', wikitext)
	return wikitext
	

def get_quote(text):

	'''
	print("debug get_quote:")
	print(text)
	print("debug end_quote\n")
	'''

	# Match the full template with multiline support
	match = re.match(r"\{\{quote-[^|]+\|(.+?)\}\}", text, flags=re.DOTALL)
	if not match:
		print("Not a valid quote template:", text)
		return ''

	out = []
	def add(*args):
		out.append(' '.join(args))

	# Split into key=value pairs
	params = match.group(1).split('|')
	kv_pairs = {}

	for param in params:
		if '=' in param:
			key, val = param.split('=', 1)
			kv_pairs[key.strip()] = val.strip()

	# Helper to remove nested templates like {{w|...}}
	def strip_nested_templates(val):
		return re.sub(r"\{\{[^|]+\|([^}]+)\}\}", r"\1", val)

	# Print available fields
	if 'passage' in kv_pairs:
		add("Quote:", kv_pairs['passage'].strip())
	if 'translation' in kv_pairs:
		add("Translation:", kv_pairs['translation'].strip())
	if 'url' in kv_pairs:
		add("Source:", kv_pairs['url'].strip())
	if 'title' in kv_pairs:
		add("Title:", kv_pairs['title'].strip())
	if 'author' in kv_pairs and kv_pairs['author']:
		author = strip_nested_templates(kv_pairs['author'].strip())
		add("Author:", author)
	if 'archiveurl' in kv_pairs and kv_pairs['archiveurl']:
		add("Archive URL:", kv_pairs['archiveurl'].strip())

	return '\n'.join(out)





def template_replacer(content):
	'''Replace text between brackets {{ ... }}'''

	# print("debug template_replacer:", repr(content))
	content = content[2:-2].replace('\n', '')
	
	# Get rid of codes likes t= nocap=
	content = preserve_glosses(content)
	
	parts = content.split('|')
	template_name = parts[0]
	# print('debug template_name', template_name)
	
	# Ignore these names:
	if template_name in IGNORE_TEMPLATES:
		# print("Ignored template:", template_name, content)
		return ''
		
	if template_name == 'suffix' and len(parts) >= 3:
		return ' +‎ '.join(parts[2:])
		
	if template_name.startswith('quote-'):
		# eprint('content=', content)		
		return get_quote('{{' + content + '}}')

	# Process noun templates
	if re.match(r"^[a-z]{2}-noun$", template_name):
		return parse_noun_template('{{' + content + '}}').title()
		
	# Special case: {{cog|en|raze}} → English raze
	if template_name == 'cog' and len(parts) >= 3:
		lang = LANGCODES.get(parts[1], parts[1])
		word = parts[2]
		return f"{lang} {word}"
		
	# Special case: {{lb|xx|label1|label2}} → (label1, label2)
	# if template_name == "lb" and len(parts) >= 3:
	#	return f"({', '.join(parts[2:])})"
		
	if template_name == 'gloss':
		return f"({', '.join(parts[1:])})" 

	# Special case: {{af|lang|morpheme1|morpheme2|t1=gloss1|t2=gloss2}} → affixed parts with glosses
	if template_name == "af":
		morphemes = []
		glosses = {}
		for part in parts[2:]:  # Skip template name and lang code
			if '=' in part:
				key, val = part.split('=', 1)
				if key.startswith('t') and key[1:].isdigit():
					glosses[int(key[1:])] = val
			else:
				morphemes.append(part)

		segments = []
		for i, morph in enumerate(morphemes, 1):
			gloss = glosses.get(i)
			if gloss:
				segments.append(f"{morph} (“{gloss}”)")
			else:
				segments.append(morph)
		return ' + '.join(segments)

	# Generic case: drop template name and all 2-letter lang codes
	rest = [
		p for p in parts[1:] if p # skip the template name
		if not re.fullmatch(r"[a-z]{2}", p)
		
	]
	rest = ', '.join(rest).strip()

	if template_name in TEMPLATE_REPLACEMENTS:
		return TEMPLATE_REPLACEMENTS[template_name].title() + ': ' + rest
	
	if not rest:
		return ''		
	if template_name not in ('ux',):
		return '(' + rest + ')'
	else:
		return rest
			

def format_lines(text):
	lines = text.strip().splitlines()
	output = []
	first = True

	for line in lines:
		line = line.rstrip()
		if line.startswith('#:'):
			# Subdefinition or related info
			output.append(' ' * 4 + line[2:].strip())
		elif line.startswith('#'):
			# Main definition
			if not first:
				output.append('')
			output.append(line[1:].strip())
			first = False
		else:
			# Any other line (e.g. not starting with #), keep as-is
			output.append(line)

	return '\n'.join(output)


'''
# slow version
def process_templates(text):
	# Process text between brackets starting with innermost and working out
	def find_innermost(text):
		stack = []
		for i in range(len(text)):
			if text[i:i+2] == '{{':
				stack.append(i)
			elif text[i:i+2] == '}}' and stack:
				start = stack.pop()
				end = i + 2
				return start, end
		return None

	while True:
		pos = find_innermost(text)
		if not pos:
			break
		start, end = pos
		inner = text[start:end]
		replacement = template_replacer(inner)
		text = text[:start] + replacement + text[end:]
	return text
'''


def process_templates(text):
	# We use a stack to store (start_index, buffer_of_inner_content)
	# print('debug process_templates', text, '\n\n\n')
	
	stack = []
	result = []
	i = 0
	while i < len(text):
		if text.startswith('{{', i):
			# Push current buffer to stack and start a new one for the inner template
			stack.append(result)
			result = []
			i += 2
		elif text.startswith('}}', i) and stack:
			# End of current template
			inner_content = ''.join(result)
			replacement = template_replacer('{{' + inner_content + '}}')
			# Pop back to previous buffer
			result = stack.pop()
			result.append(replacement)
			i += 2
		else:
			# Normal character, just append
			result.append(text[i])
			i += 1

	# If there are unmatched '{{', just append them back (optional safety)
	while stack:
		prev = stack.pop()
		prev.append('{{' + ''.join(result))
		result = prev


	result = ''.join(result)
	# print('debug result', result, '\n\n\n')
	
	return result


def replace_brackets(m):
	def capitalize_first(s: str) -> str:
		return s[0].upper() + s[1:] if s else s
		
	if m.group(2):  # has a pipe ( [[text|display]] )
		return f"{capitalize_first(m.group(1))}, {capitalize_first(m.group(2))}"
	else:  # no pipe ( [[word]] )
		return capitalize_first(m.group(1))
		

def clean_wikitext(text):
	# Clean_wikitext is throwing away formatting without saving much filesize, 
	# So we keep the original in the database just in case this function needs tweaking later
	# or the we want to display it differently (perhaps in a GUI someday?)
	
	
	# Remove the "</text>" tag
	text = text.replace("</text>", "")

	# Remove unwanted sections
	# text = re.sub(r"=+\s*(Conjugation|Descendants|Pronunciation|References|Further reading)\s*=+.*?(?==+[^=]|$)", "", text, flags=re.DOTALL)	
	text = re.sub(r"=+\s*(Conjugation|Descendants|Pronunciation|References|Further reading)\s*=+.*?(?=\n=+|$)", "", text, flags=re.DOTALL )
	# print('debug unwanted sections', text, '\n\n\n')
	
	

	# Replace [[text|display]] with "text, display"
	# text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\1, \2", text)
	# Replace [[word]] with word
	# text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
	text = re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", replace_brackets, text)	
	

	# Replace text between brackets {{ ... }}
	# text = re.sub(r"\{\{([^\{\}]+?)\}\}", template_replacer, text)
	# Catch templates with nesting:	
	# text = regex.sub(r"\{\{((?:[^{}]+|(?R))*)\}\}", template_replacer, text)
	text = process_templates(text)
	

	# Remove <ref>...</ref> and <references/>
	text = re.sub(r"&lt;ref&gt;.*?&lt;/ref&gt;", "", text)
	text = re.sub(r"&lt;references\s*/&gt;", "", text)
	
	# Remove blank sections:
	text = re.sub(r'(=+[^=]+=+)\s*(?=\n=+)', '', text)
	
	# Clean up excessive blank lines
	text = re.sub(r"\n{3,}", "\n\n", text)
	
	# Decode HTML entities
	# text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
	text = html.unescape(text)
	
	
	# Replace quotes around '''word'''
	# text = text.replace("'''", '"')
	
	# Tabs
	text = format_lines(text)
	
	# Remove blank lines immediately following section headers
	# text = re.sub(r"(={2,}[^=]+={2,})\n+", r"\1\n", text)
	text = re.sub(r"(={2,}[^=]+={2,})\n\s*\n", r"\1\n", text)

	return text.strip()
	


def tester():
	text = """
{{was wotd|2008|February|20}}
{{wikipedia}}

===Etymology===
From {{m|en|bailie||bailiff}} and {{m|en|wick||dwelling}}, from {{inh|en|ang|wīc}}.

===Pronunciation===
* {{enPR|bā'lĭ-wĭk}}, {{IPA|en|/ˈbeɪ.lɪ.wɪk/}}
* {{audio|en|en-us-bailiwick.ogg|a=US}}

===Noun===
{{en-noun}}

# The [[district]] within which a [[bailie]] or [[bailiff]] has [[jurisdiction]].
#: ''The [[w:Bailiwick of Jersey|Bailiwick of Jersey]].''
# A person's concern or [[sphere]] of operations, their area of [[skill]] or [[authority]].
#* {{quote-book|en|year=1961|author=w:Eleanor Roosevelt|title=The Autobiography of Eleanor Roosevelt
|passage=I established the fairly well-understood pattern that affairs of state were not in my '''bailiwick'''.}}
#* {{quote-web|1=en|author=Alex McLevy|title=Marilynne Robinson finds transcendence in the stunning, soul-searching ''Jack''|work=w:The A.V. Club|url=https://aux.avclub.com/marilynne-robinson-finds-transcendence-in-the-stunning-1845132848|date=September 28, 2020|passage=Jack is full of these insights, thoughtful turns of phrase from a character whose perpetual struggle between wastrel and righteous is all too familiar a '''bailiwick''' for the universal insecurities of the human condition.|accessdate=3 October 2020|archiveurl=https://web.archive.org/web/20201001010115/https://aux.avclub.com/marilynne-robinson-finds-transcendence-in-the-stunning-1845132848|archivedate=1 October 2020}}

====Synonyms====
* {{sense|area or subject of authority or involvement}} {{l|en|domain}}, {{l|en|department}}, {{l|en|jurisdiction}}, {{l|en|sphere}}, {{l|en|province}}, {{l|en|territory}}, {{l|en|turf}}, {{l|en|pale}}, {{l|en|wheelhouse}}.

====Related terms====
* {{l|en|bailie}}
* {{l|en|bailiff}}

====Translations====
{{trans-top|precincts within which a bailiff has jurisdiction}}
* Dutch: {{t+|nl|meierij|f}}, {{t+|nl|baljuwschap|n}}
* French: {{t+|fr|bailliage|m}}
* German: {{t+|de|Vogtei}}
* Icelandic: {{t|is|fógetaumdæmi|n}}
* Italian: {{t|it|bailiato|m}}
* Manx: {{t|gv|bayleeaght|f}}, {{t|gv|bayleeys|m}}
* Polish: {{t+|pl|baliwat}}
* Russian: {{t|ru|бейливик|m}}
* Spanish: {{t|es|bailía|f}}
* Swedish: {{t+|sv|verksamhetsområde|n}}
{{trans-bottom}}

{{trans-top|area or subject of authority or involvement}}
* Dutch: {{t+|nl|gezag|n}}, {{t+|nl|domein|n}}, {{t+|nl|competentie|f}}
* French: {{t+|fr|bailliage|m}}, {{t+|fr|compétence}}, {{t+|fr|autorité}}
* Icelandic: {{qualifier|area of knowledge}} {{t|is|þekkingarsvið|n}}, {{qualifier|occupational area}} {{t+|is|starfssvið|n}}, {{qualifier|field of interest}} {{t|is|áhugasvið|n}}, {{qualifier|field of competence}} {{t|is|valdsvið|n}}
* Serbo-Croatian: {{t+|sh|nadležnost|f}}
* Spanish: {{t|es|bailía|f}}
{{trans-bottom}}

===References===
* {{R:Webster 1913}}

{{cln|en|terms suffixed with -wick}}</text>
	"""
	
	eprint("Source text:")
	eprint(text)
	
	eprint("\n"*10)
	eprint("Clean wikitext:")
	eprint(clean_wikitext(text))


if __name__ == "__main__":
	tester()
