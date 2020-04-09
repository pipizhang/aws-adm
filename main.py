# -*- coding: utf-8 -*-
import boto3
import time
import click
from botocore.exceptions import ClientError
from pprint import pprint

class EC2Instance(object):
    fields = ['id', 'name', 'ip']

    def __init__(self, **kwargs):
        self.ec2 = boto3.client('ec2')
        self._values = {}
        if kwargs:
            for k, v in kwargs.items():
                self[k] = v

    def __getattr__(self, key):
        return self._values[key]

    def __setitem__(self, key, value):
        if key in self.fields:
            self._values[key] = value

    def status(self):
        res = self.ec2.describe_instances()
        for row in res['Reservations']:
            ins = row['Instances'][0]
            if ins['InstanceId'] == self.id:
                return ins['State']['Name']
        return 'unkonwn'

    def is_running(self):
        return self.status() == 'running'

    def is_stopped(self):
        return self.status() == 'stopped'


class EC2Manager(object):

    def __init__(self):
        self.ec2 = boto3.client('ec2')

    def test(self, instance):
        pprint(instance.status())

    def stop_instance(self, instance):
        if instance.is_stopped():
            print('{} is stopped already'.format(instance.ip))
            return
        else:
            print('> stop ec2: {}'.format(instance.id))

        # Do a dryrun first to verify permissions
        try:
            self.ec2.stop_instances(InstanceIds=[instance.id], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise
        # Dry run succeeded, call stop_instances without dryrun
        try:
            response = self.ec2.stop_instances(InstanceIds=[instance.id], DryRun=False)
            for i in range(1, 100):
                time.sleep(2)
                print(instance.status())
                if instance.is_stopped():
                    print('success')
                    break

        except ClientError as e:
            print(e)

    def start_instance(self, instance):
        if instance.is_running():
            print('{} is running already'.format(instance.ip))
            return

        print('> start ec2: {}'.format(instance.id))

        # Do a dryrun first to verify permissions
        try:
            self.ec2.start_instances(InstanceIds=[instance.id], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise
        # Dry run succeeded, call stop_instances without dryrun
        try:
            response = self.ec2.start_instances(InstanceIds=[instance.id], DryRun=False)
            for i in range(1, 100):
                time.sleep(2)
                print(instance.status())
                if instance.is_running():
                    print('success')
                    break

        except ClientError as e:
            print(e)

    def run(self, command):
        res = self.ec2.describe_instances()
        _exec = self.start_instance if command == 'start' else self.stop_instance

        for row in res['Reservations']:
            ins = row['Instances'][0]
            if ins['PrivateIpAddress'].startswith('192.168.'):
                _exec(EC2Instance(
                    id=ins['InstanceId'],
                    ip=ins['PrivateIpAddress']
                ))

"""""
CLICK
"""""
@click.group()
def cli():
    pass

@cli.command()
def start():
    click.echo('Start ec2 instances')
    EC2Manager().run('start')

@cli.command()
def stop():
    click.echo('Stop ec2 instances')
    EC2Manager().run('stop')


"""
RUN
"""
if __name__ == '__main__':
    cli()


