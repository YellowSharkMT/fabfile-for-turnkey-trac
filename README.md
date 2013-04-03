# Fabfile for TurnKey Trac
A set of functions for Python+Fabric that expedite creating/removing projects from a [TurnKey Trac VM](http://www.turnkeylinux.org/trac). Currently it's heavily-focused on the Git end of things, and so Mercurial and Bazaar are totally untested, and Subversion will *probably* work, but not guaranteed (yet). And if you're not familiar with the Trac VM, it's as simple as downloading the ISO, and firing up a new box in VirtualBox or your own VM software of choice.

Special credit to blogger/coder ClearStream. I relied heavily upon this blog post: http://curiosityandfun.wordpress.com/2012/02/03/setting-up-a-multi-project-multi-user-git-repo-with-turnkey-trac/. If you read through that post, you'll see that adding/removing a Trac project isn't just a 1-line affair. And that's what this fabfile attempts to help with.

Note: It's assumed that you are competent with managing a VM, using [Fabric](http://fabfile.org), and that you have root SSH access to a TurnKey Trac VM. You can check this package out to any folder you like, and just run `fab -l` to make sure things jive. Before starting though, you'll need to create a copy of the `settings_example.py` file, name it `settings.py`, and update the SSH connection string for your Trac VM.

Another Note: This particular setup process requires a plugin for Trac: [AccountManager plugin for Trac](https://bitbucket.org/alexandrul/trac-accountmanager-plugin/overview). Be sure to first set this up on your Trac box before proceeding. The directions found in the package's README file are simple & perfect, and if you have any questions about installing a plugin to Trac, just Google "turnkey trac plugin". If you don't install this plugin, you'll have weirdness when you try to log in.

## Usage:

### setup(project_name, project_type = 'git')

Creates a project, via `trac-initproject`, then creates a user & group for the project (You will be prompted to enter a password for the user, currently the username is taken from the project name. So if you provide "my-cool-site" as the project name, this translates to the SSH connection string later (my-cool-site@*appliance_ip*), and the group is named `"project-" + project_name`, so "project-my-cool-site", in the previous example.

After creating the project and the user/group, it updates a few config files: the .git/config file, and then the conf/trac.ini file for the new project. (Located in `/var/local/lib/trac/PROJECT_TYPE-PROJECT_NAME`.)

Note: When you visit your project's Trac page now, you'll see that it offers you to login. Use the username "admin", and the password - I believe - is the VM's root password. I'm not positive of that, but I'm pretty darn sure. I know - I'm not keen on that either, however it's something I'll be figuring out shortly. One thing I can tell you is that it uses info from the /etc/trac/htpasswd file. I'm not positive what I'll be able to do there, but

Example usage:

- `fab setup:my-cool-thing,git`
- `fab setup:client-a,svn`

### remove(project_name, project_type = 'git')

Removes the project by deleting the associated folders, then optionally deleting the user/group that was created for the project. (Asks you to confirm delete during execution.)

Example usage:

- `fab remove:project-54,git`

## To-Do List

- Figure out the deal with admin/root password... wow.
- Test Subversion, make sure it works
- ... TBD!