import os, sys
import sphinx_rtd_theme as theme
sys.path.insert(0, os.path.dirname(__file__))
source_suffix = '.rst'
master_doc = 'index'
project = u'git-spindle'
copyright = u'2012-2018, Dennis Kaarsemaker'
version = '3.4'
release = '3.4.4'
exclude_patterns = ['_build']
pygments_style = 'sphinx'
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_options = {
}
html_theme_path = [theme.get_html_theme_path()]
html_show_sourcelink = False
html_show_sphinx = False
extensions = ['ansicolor']
man_pages = [
    ('github', 'git-hub', 'GitHub integration', 'Dennis Kaarsemaker', '1'),
    ('gitlab', 'git-lab', 'GitLab integration', 'Dennis Kaarsemaker', '1'),
    ('bitbucket', 'git-bb', 'BitBucket integration', 'Dennis Kaarsemaker', '1'),
    ('bitbucket', 'git-bucket', 'BitBucket integration', 'Dennis Kaarsemaker', '1'),
]
