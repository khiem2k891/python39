import paramiko
import os
import subprocess
import tarfile
import argparse
import csv

def create_user(ip, username, password, new_username, new_password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username='root', password='1')

        # Check if the user already exists
        stdin, stdout, stderr = ssh.exec_command(f'id -u {new_username} 2>/dev/null')
        output = stdout.read().decode('utf-8').strip()
        if output:
            print(f"User {new_username} already exists on {ip}.")
            return

        # Create the user
        stdin, stdout, stderr = ssh.exec_command(f'sudo useradd {new_username}')
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()
        if error:
            print(f"Error occurred while creating user {new_username} on {ip}: {error}")
        else:
            print(f"User {new_username} created successfully on {ip}.")

        # Set password for the user
        stdin, stdout, stderr = ssh.exec_command(f'sudo passwd {new_username}')
        stdin.write(f'{new_password}\n')
        stdin.write(f'{new_password}\n')
        stdin.flush()
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()
        if error:
            print(f"Error occurred while setting password for user {new_username} on {ip}: {error}")
        else:
            print(f"Password set successfully for user {new_username} on {ip}.")

    except Exception as e:
        print(f"Error occurred while connecting to {ip}: {e}")

def check_python39(ip):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username='root', password='1')

        # Check if python3.9 is installed
        stdin, stdout, stderr = ssh.exec_command('which python3.9')
        python3_path = stdout.read().decode('utf-8').strip()
        if python3_path:
            print(f"The server with ip {ip} has python3.9 at {python3_path}")
            # Check python3.9 version
            stdin, stdout, stderr = ssh.exec_command('python3.9 --version')
            python3_version = stdout.read().decode('utf-8').strip()
            if python3_version:
                # Write results to CSV file
                with open('python_versions.csv', 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([ip, python3_version, python3_path])
            return True

        # Check if python39 package is in the local repository
        stdin, stdout, stderr = ssh.exec_command('dnf search python39')
        output = stdout.read().decode('utf-8').strip()
        if 'python39' in output:
            print(f"The server with {ip} has python39 package in the local repository")
            # Install python39
            stdin, stdout, stderr = ssh.exec_command('sudo dnf install -y python39')
            output = stdout.read().decode('utf-8').strip()
            print(output)
            return True

        # Copy Python-3.9.12.tgz from workstation to server
        sftp = ssh.open_sftp()
        sftp.put('Python-3.9.12.tgz', '/tmp/Python-3.9.12.tgz')
        sftp.close()

        # Extract Python-3.9.12.tgz
        stdin, stdout, stderr = ssh.exec_command('tar -xzf /tmp/Python-3.9.12.tgz -C /tmp')
        output = stdout.read().decode('utf-8').strip()
        print(output)

        # Run customized commands
        stdin, stdout, stderr = ssh.exec_command("yum groupinstall 'Development Tools'")
        stdin, stdout, stderr = ssh.exec_command('cd /tmp/Python-3.9.12')
        stdin, stdout, stderr = ssh.exec_command('./configure && make && make install')

        # Check if python3.9 is installed
        stdin, stdout, stderr = ssh.exec_command('python3.9 --version')
        python3_version = stdout.read().decode('utf-8').strip()
        if python3_version:
            # Write results to CSV file
            with open('python_versions.csv', 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([ip, python3_version, python3_path])
            return True

    except Exception as e:
        print(f"Error occurred while connecting to {ip}: {e}")


def main():
    with open('ipslist.txt', 'r') as f:
        ips = f.read().strip().split(',')

    # Write headers to CSV file
    with open('python_versions.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["IP Address", "Python 3 Version", "Python 3 Path"])

    for ip in ips:
        create_user(ip, 'root', '1', 'ansible', 'vid@12345678')
        check_python39(ip)

if __name__ == '__main__':
    main()
