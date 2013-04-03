# Fabfile for Turnkey Trac Appliance
# Author: YellowShark (http://yellowsharkmt.com)
#
# URL for the TurnKey Trac VM: http://www.turnkeylinux.org/trac
# This is a set of functions mostly based upon: http://curiosityandfun.wordpress.com/2012/02/03/setting-up-a-multi-project-multi-user-git-repo-with-turnkey-trac/
#
# Fair warning: I develop with SVN and Git, but never with Bazaar or Mercurial. Therefore, I can't guarantee
# that all functionality for Hg & Bzr will work. The things I suspect might break are the bits where permissions
# get assigned to the .git directory. I'm not sure how Hg & Bzr store their info (currently), so some of these parts
# might fail. However, I've tried to create this so that if there's any doubt about doing something, then I limit
# that functionality to known project types.

from __future__ import with_statement
from fabric.api import settings as fab_settings
from fabric.api import *
import sys, re
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, append, contains
import fileinput

# Leaving this as True is generally harmless, it simply allows you to enter a connection
# name from your .ssh/config file as a value for env.host_string (set this in settings.hosts)
env.use_ssh_config = True

try:
	from settings import COLLATERAL_DIR, hosts, TMP_DIR
except:
	print('Unable to load settings file. Have you created one?')
	sys.exit(0)

#= [Public Functions] ===========================================
@task
def setup(project_name = False, project_type='git', **kwargs):
	""" Initializes a project on the Trac VM. :project_name,project_type
	"""
	valid, message = _validate_project_name_and_type(project_name, project_type)
	if not valid:
		print(message)
		sys.exit(0)

	_prod()

	# init the project
	cmd_vars = {
		'project_name':project_name,
		'project_type':project_type,
	}
	run('trac-initproject %(project_type)s %(project_name)s' % cmd_vars)
	run('trac-admin /var/local/lib/trac/%(project_type)s-%(project_name)s/ permission remove authenticated \'*\'' % cmd_vars)
	run('trac-admin /var/local/lib/trac/%(project_type)s-%(project_name)s/ permission remove anonymous \'*\'' % cmd_vars)

	_adduser(project_name, project_name, project_type)
	_update_files(project_name, project_type)

	run('service apache2 restart')
	print('---------------')
	print('Trac project setup is complete. Have fun!')

@task
def remove(project_name = False, project_type = 'git'):
	""" Removes a project on the Trac VM. :project_name,project_type
	"""
	valid, message = _validate_project_name_and_type(project_name, project_type)
	if not valid:
		print(message)
		sys.exit(0)

	cmd_vars = {
		'project_name':project_name,
		'project_type':project_type,
	}
	if confirm('This will delete the `%(project_name)s` %(project_type)s project. Are you REALLY sure?' % cmd_vars):

		_prod()

		# Delete directories.........
		with cd('/var/local/lib/trac'):
			if exists('%(project_type)s-%(project_name)s' % cmd_vars):
				print('Deleting directory: /var/local/lib/trac/%(project_type)s-%(project_name)s...' % cmd_vars)
				run('rm -rf %(project_type)s-%(project_name)s' % cmd_vars)
			else:
				print('Could not locate directory: /var/local/lib/trac/%(project_type)s-%(project_name)s' % cmd_vars)

		with cd('/etc/trac'):
			if exists('%(project_type)s-%(project_name)s.ini' % cmd_vars):
				print('Deleting file: %(project_type)s-%(project_name)s.ini...' % cmd_vars)
				run('rm -rf %(project_type)s-%(project_name)s.ini' % cmd_vars)
			else:
				print('Could not locate file: %(project_type)s-%(project_name)s.ini' % cmd_vars)

		with cd('/srv/repos/%(project_type)s' % cmd_vars):
			if exists('%(project_name)s' % cmd_vars):
				print('Deleting directory: /srv/repost/%(project_type)s/%(project_name)s...' % cmd_vars)
				run('rm -rf %(project_name)s' % cmd_vars)
			else:
				print('Could not locate directory: /srv/repost/%(project_type)s/%(project_name)s...' % cmd_vars)

		# Delete users/group...
		if confirm('Do you wish to also delete the user?'):
			_remove_user_and_group(project_name, project_name, project_type)

		print('Done deleting the `%(project_name)s` project.' % cmd_vars)

#@task
def remove_user_and_group(username = False, project_name = False, project_type = 'git'):
	""" Wrapper function for developing _remove_user_and_group
	"""
	_prod()
	_remove_user_and_group(username, project_name, project_type)

def _remove_user_and_group(username = False, project_name = False, project_type = 'git'):
	cmd_vars = {
	'username':username,
	'project_name':project_name,
	'project_type':project_type,
	}
	with fab_settings(warn_only=True):
		run('deluser %(username)s' % cmd_vars)
		run('groupdel project-%(project_name)s' % cmd_vars)

#- [Private Functions] -------------------------------------------
def _prod():
	env.host_string = hosts.get('prod')

#---
def _validate_project_name_and_type(project_name = False, project_type='git', **kwargs):

	# Check that a project_name was supplied
	if not project_name:
		return (False, 'You must provide a project name.')

	# Validate project name
	m = re.match('^[\w\d][\w\d\-\.]+[\w\d]$', project_name)
	if not m:
		return (False, 'Valid project names can contain only letters and numbers. Hyphens and periods are allowed, but not as a first or last character.')

	# Validate project_type
	if not re.match('^git|svn|bzr|hg$', project_type):
		return (False, 'Valid types are: git, svn, bzr, hg')

	return (True, 'Project name & type are valid.')

#---
def _adduser(username = False, project_name = False, project_type = 'git'):
	cmd_vars = {
		'username':username,
		'project_name':project_name,
		'project_type':project_type,
	}
	run('adduser %(username)s' % cmd_vars)

	_adduser_to_group(username, project_name, project_type)

	print('Finished adding user, creating group, and setting permissions for the `%(project_name)s` project.' % cmd_vars)

#---
#@task
def adduser_to_group(username, project_name, project_type):
	""" Wrapper function for developing _add_user_to_group
	"""
	_adduser_to_group(username, project_name, project_type)

def _adduser_to_group(username, project_name, project_type):
	cmd_vars = {
		'username':username,
		'project_name':project_name,
		'project_type':project_type,
	}
	run('groupadd project-%(project_name)s' % cmd_vars)
	run('usermod -a -G project-%(project_name)s %(username)s' % cmd_vars)

	with cd('/srv/repos/%(project_type)s/%(project_name)s' % cmd_vars):
		run('chown -R www-data.%(project_name)s .%(project_type)s' % cmd_vars)
		run('chmod -R 771 .%(project_type)s' % cmd_vars)

#---
#@task
def update_files(project_name, project_type):
	""" Wrapper function for developing the _update_files functionality. """
	_prod()
	_update_files(project_name, project_type)


def _update_files(project_name, project_type):
	cmd_vars = {
		'project_name':project_name,
		'project_type':project_type,
	}

	# Git-specific setup
	if project_type == 'git':
		# allow push to checked-out branch
		target = '/srv/repos/%(project_type)s/%(project_name)s/.git/config' % cmd_vars
		if exists(target):
			print('Updating the .git/config file...')
			if not contains(target, '\[receive\]\ndenyCurrentBranch \= false'):
				update_code = "[receive]\ndenyCurrentBranch = false"
				append(target, update_code)
				print('Finished updating the .git/config file.')
			else:
				print('.git/config file already appears to be updated.')
		else:
			print('Could not locate the .git/config file.')

	# Create new trac.ini file
	with cd('/var/local/lib/trac/%(project_type)s-%(project_name)s/conf/' % cmd_vars):
		if exists('trac.ini'):
			print('Updating the trac.ini file...')
			insert_the_text = False
			inserted_components_text = False
			update_account_manager = False
			updated_account_manager_section = False

			# I'm not as happy with the iteration-style i've got going on here, compared to the sed usage above...
			# it kinda seems like I should be using sed to update the blocks, instead. actually sed is horrible in
			# multi-line scenarios, iterating is a better, albeit clunkier option.
			target = '/var/local/lib/trac/%(project_type)s-%(project_name)s/conf/trac.ini' % cmd_vars
			local_target = TMP_DIR + 'trac.ini.tmp'
			get(target, local_target)
			for line in fileinput.input(local_target, inplace=1, backup='.bak'):
			#for line in open(local_target, 'r'):
				if not inserted_components_text: # limit the regex testing we do, so we just find it and then quickly dump
					# the rest of the file
					if re.match('\[components\]', line):
						insert_the_text = True
						print line,
					else:
						if insert_the_text:
							# do stuff here to insert the new copy
							file_to_insert = open(COLLATERAL_DIR + 'trac.ini.components-chunk.txt','r')
							print('# Updated automatically by Fabfile-for-Trac.')
							for line_to_insert in file_to_insert:
								m = re.match('^(.*?)[\n]+', line_to_insert)
								if not m:
									print line_to_insert,
								else:
									print(m.group(1) + "\n"),

								# if not m.groups(0):
								# 	print line_to_insert
								# else:
								# 	print m.groups(0)
							print("\n" + '# End of code created by Fabfile-for-Trac.' + "\n"),
							inserted_components_text = True # causes a break from any further regex testing in this loop

						insert_the_text = False
						print line,

			print('... Updated the [component] block...')


			if contains(local_target, '\[account-manager\]'):
				print('You will have to update the trac.ini->[account-manager] block manually, it already exists.')
			else:
				with open(local_target, "a") as f:
					f.write("\n" + '# Updated automatically by Fabfile-for-Trac.' + "\n")
					f.write('[account-manager]' + "\n")
					file_to_insert = open(COLLATERAL_DIR + 'trac.ini.account-manager-chunk.txt','r')
					for line_to_insert in file_to_insert:
						m = re.match('^(.*?)[\r\n]+', line_to_insert)
						if not m:
							f.write(line_to_insert + "\n")
						else:
							f.write(m.group(1) + "\n")

					f.write('# End of code created by Fabfile-for-Trac.' + "\n")

			print('... Updated the [account-manager] block...')
			put(local_target, target)
			put(local_target+'.bak', target+'.bak')

			print('Finished updating & uploading the trac.ini file.')

		print('Finished updating all files.')







