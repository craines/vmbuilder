import subprocess
import os
import urllib.request

from tqdm import tqdm


def run_command(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
    return p.decode('utf-8')


def run_command_with_out_output(command):
    response = run_command(command)
    print(response)


def run_command_get_latest_vmid():
    return run_command('pvesh get /cluster/nextid')


def run_command_get_vmids():
    result = run_command(
        "pvesh get /cluster/resources | awk '{print $2}' | sed '/storage/d' | sed '/node/d' | sed '/id/d' | sed '/./,/^$/!d' | cut -d '/' -f 2 | sed '/^$/d'")
    return list(filter(None, result.split('\n')))


def run_command_get_storages():
    result = run_command("awk '{if(/:/) print $2}' /etc/pve/storage.cfg")
    return list(filter(None, result.split('\n')))


def run_command_get_storages_path():
    result = run_command("awk '{if(/path/) print $2}' /etc/pve/storage.cfg")
    return list(filter(None, result.split('\n')))


def run_command_networks():
    result = run_command("awk '{if(/vmbr/) print $2}' /etc/network/interfaces")
    return list(filter(None, result.split('\n')))


def get_vmid():
    print("*** Taking a 5-7 seconds to gather information ***")

    lastest_vmid = run_command_get_latest_vmid()
    vmids = run_command_get_vmids()

    print("Enter desired VM ID number or press enter to accept default of %s" % lastest_vmid)

    while True:
        new_vmid = input("\nNew VM ID number: ")
        if (len(new_vmid) <= 0):
            break

        if (new_vmid in vmids):
            print(
                "\n Enter a different number because either you are using it or reserved by the sysem New VM ID number \n")
        else:
            lastest_vmid = new_vmid
            break

    return int(lastest_vmid)


def get_password():
    password = input("\nPlease enter password for the user: ")
    password_confirmation = input("\nPlease repeat password for the user: ")

    if (password != password_confirmation):
        print("\n Please try again passwords did not match \n")
        return get_password()

    return run_command("openssl passwd -1 -salt SaltSalt %s" % password)


def get_storage():
    storages = run_command_get_storages()
    print("Please select the storage the VM will run on?")

    while True:
        for key, value in enumerate(storages):
            print("%s) %s" % (key + 1, value))

        storage = input("#? ")

        if storage:
            try:
                storage = storages[int(storage) - 1]
                print("The storage you selected for the VM is %s" % storage)
                return storage
            except(IndexError):
                print("Incorrect Input Selected")
        else:
            pass


def get_iso_storage():
    storages = run_command_get_storages_path()
    print("Please select ISO storage location")

    path = "template/iso"

    while True:
        for key, value in enumerate(storages):
            print("%s) %s/%s" % (key + 1, value, path))

        storage = input("#? ")

        if storage:
            try:
                storage = "%s/%s" % (storages[int(storage) - 1], path)
                print("The cloud image will be downloaded to  %s  or look there if already downloaded" % storage)
                return storage
            except(IndexError):
                print("Incorrect Input Selected")
        else:
            pass


def get_snippets_storage():
    storages = run_command_get_storages_path()
    print("""
Please select the storage that has snippets available
If you pick one that does not have it enabled the VM being created will not have all the
user settings (user name, password , keys) so if you need to check in the GUI click on Datacenter
then click on storage and see if enabled, if not you need to enable it on the storage you want it
to be placed on.  There will be two questions for snippet setup. One for the actual locaiton to put the user.yaml and the
second for the storage being used for snippets.
        """)

    path = "snippets"

    while True:
        for key, value in enumerate(storages):
            print("%s) %s/%s" % (key + 1, value, path))

        storage = input("#? ")

        if storage:
            try:
                storage = "%s/%s" % (storages[int(storage) - 1], path)
                print(
                    "The snippet storage location will be %s here, which will hold the user data yaml file for each VM" % storage)
                print("""
Now that we have selected the snippet storage path (%s) we need to actually select the storage that this path is on.
Make sure the path picked and the storage picked are one in the same or it will fail.
example /var/lib/vz/snippets/ is local storage
                    """ % storage)
                return storage
            except(IndexError):
                print("Incorrect Input Selected")
        else:
            pass


def get_network():
    networks = run_command_networks()
    print("Please select VMBR to use for your network?")

    while True:
        for key, value in enumerate(networks):
            print("%s) %s" % (key + 1, value))

        network = input("#? ")

        if network:
            try:
                network = networks[int(network) - 1]
                print("Your network bridge will be on %s" % network)
                return network
            except(IndexError):
                print("Incorrect Input Selected")
        else:
            pass


def get_vlan():
    while True:
        has_vlan = input("\nDo you need to enter a VLAN number? [Y/n]: ").lower()
        if has_vlan == 'y':
            return input("\nEnter desired VLAN number for the VM: ")
        elif has_vlan == 'n':
            return None
        else:
            pass


def get_network_config():
    has = input("\nEnter Yes/Y to use DHCP for IP or Enter No/N to set a static IP address: ").lower()

    if (has == 'n'):

        while True:
            ip = input("\nEnter IP address to use (format example 192.168.1.50/24): ")
            ip_confirmation = input("\nEnter IP address to use (format example 192.168.1.50/24): ")

            if (ip != ip_confirmation):
                print("\n\nPlease try again IP addresses did not match\n\n")
                pass

            gateway = input("\nEnter gateway IP address to use (format example 192.168.1.1): ")
            gateway_confirmation = input("\nPlease repeate gateway IP address to use (format example 192.168.1.1): ")

            if (gateway != gateway_confirmation):
                print("\n\nPlease try again gateway IP addresses did not match\n\n")
                pass

            return ip, gateway

    elif (has == 'y'):
        return 'dhcp', None
    else:
        return get_network_config()


def get_disk_size():
    while True:
        size = input("\nSet disk size in GB (exampe 2 for adding 2GB to the size), default is 50: ")
        if size:
            if size.isnumeric:
                return int(size)
            else:
                print("invalid disk size")
                pass
        else:
            return 50


def get_ram():
    while True:
        size = input("\nEnter how much memory (example 2048 is 2Gb of memory), default is 2048: ")
        if size:
            if size.isnumeric:
                return int(size)
            else:
                print("invalid input")
                pass
        else:
            return 2048


def get_cpu_cores():
    while True:
        size = input("\nEnter number of cores, default is 2: ")
        if size:
            if size.isnumeric:
                return int(size)
            else:
                print("invalid input")
                pass
        else:
            return 2


def get_ssh_key():
    has = input("\nDo you want to add a ssh key by entering the path to the key? (Enter Y/n): ").lower()

    if has == 'y':

        while True:
            path = input("\nEnter the path and key name (path/to/key.pub): ")
            if os.path.isfile(path):
                with open(path, 'r') as f:
                    lens = f.readlines()
                    if len(lens) > 0:
                        return lens[0]
            else:
                print("\n\nDoes not exist, try again please.\n\n")
                pass

    elif has == 'n':
        return None
    else:
        return get_ssh_key()


def enable_password_authenticator():
    has = input("\nDo you want ssh password authentication (Enter Y/n)? ").lower()

    if has == 'y':
        return True
    elif has == 'n':
        return False
    else:
        return enable_password_authenticator()


def install_qemu_gust_agent():
    has = input("\nWould you like to install qemu-gust-agent on first run? (Enter Y/n) ").lower()

    if (has == 'y'):
        return True
    elif (has == 'n'):
        return False
    else:
        return install_qemu_gust_agent()


def enable_protection():
    print("""
          \n\n
            PLEASE READ - THIS IS FOR PROXMOX CLUSTERS 
            This will allow you to pick the Proxmox node for the VM to be on once it is completed 
            BUT 
            It will start on the proxmox node you are on and then it will use 
            qm migrate to the target node (JUST FYI)
            \n\n
          """)

    has = input("\nDo you want VM protection enabled[Y/n]").lower()

    if (has == 'y'):
        return True
    elif (has == 'n'):
        return False
    else:
        return enable_protection()


def get_distros():
    distro_list = [
        {
            "name": "Ubuntu Hirsute Hippo 21.04 Cloud Image",
            "url": "https://cloud-images.ubuntu.com/hirsute/current/hirsute-server-cloudimg-amd64-disk-kvm.img",
            "file_name": "hirsute-server-cloudimg-amd64-disk-kvm.img"
        },
        {
            "name": "Ubuntu Groovy 20.10 Cloud Image",
            "url": "https://cloud-images.ubuntu.com/daily/server/groovy/current/groovy-server-cloudimg-amd64-disk-kvm.img",
            "file_name": "groovy-server-cloudimg-amd64-disk-kvm.img"
        },
        {
            "name": "Ubuntu Focal 20.04 Cloud Image",
            "url": "https://cloud-images.ubuntu.com/focal/current/focal-server-cloudimg-amd64-disk-kvm.img",
            "file_name": "focal-server-cloudimg-amd64-disk-kvm.img"
        },
        {
            "name": "Ubuntu Minimal Focal 20.04 Cloud Image",
            "url": "https://cloud-images.ubuntu.com/minimal/releases/focal/release/ubuntu-20.04-minimal-cloudimg-amd64.img",
            "file_name": "ubuntu-20.04-minimal-cloudimg-amd64.img"
        },
        {
            "name": "CentOS 7 Cloud Image",
            "url": "http://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2",
            "file_name": "CentOS-7-x86_64-GenericCloud.qcow2"
        },
        {
            "name": "AlmaLinux 8 Generic Cloud latest",
            "url": "https://repo.almalinux.org/almalinux/8/cloud/x86_64/images/AlmaLinux-8-GenericCloud-latest.x86_64.qcow2",
            "file_name": "AlmaLinux-8-GenericCloud-latest.x86_64.qcow2"
        },
        {
            "name": "AlmaLinux 9 Generic Cloud latest",
            "url": "https://repo.almalinux.org/almalinux/9/cloud/x86_64/images/AlmaLinux-9-GenericCloud-latest.x86_64.qcow2",
            "file_name": "AlmaLinux-9-GenericCloud-latest.x86_64.qcow2"
        },
        {
            "name": "Debian 12 Cloud Image",
            "url": "https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-amd64.qcow2",
            "file_name": "debian-12-generic-amd64.qcow2"
        },
        {
            "name": "Debian 11 Cloud Image",
            "url": "https://cdimage.debian.org/cdimage/cloud/bullseye/latest/debian-11-generic-amd64.qcow2",
            "file_name": "debian-11-generic-amd64.qcow2"
        },
        {
            "name": "Debian 10 Cloud Image",
            "url": "https://cdimage.debian.org/cdimage/openstack/current-10/debian-10-openstack-amd64.qcow2",
            "file_name": "debian-10-openstack-amd64.qcow2"
        },
        {
            "name": "Debian 9 Cloud Image",
            "url": "https://cdimage.debian.org/cdimage/openstack/current-9/debian-9-openstack-amd64.qcow2",
            "file_name": "debian-9-openstack-amd64.qcow2"
        },
        {
            "name": "Ubuntu 18.04 Bionic Image",
            "url": "https://cloud-images.ubuntu.com/bionic/current/bionic-server-cloudimg-amd64.img",
            "file_name": "bionic-server-cloudimg-amd64.img"
        },
        {
            "name": "CentOS 8 Cloud Image",
            "url": "https://cloud.centos.org/centos/8/x86_64/images/CentOS-8-GenericCloud-8.2.2004-20200611.2.x86_64.qcow2",
            "file_name": "CentOS-8-GenericCloud-8.2.2004-20200611.2.x86_64.qcow2"
        },
        {
            "name": "Fedora 32 Cloud Image",
            "url": "https://download.fedoraproject.org/pub/fedora/linux/releases/32/Cloud/x86_64/images/Fedora-Cloud-Base-32-1.6.x86_64.qcow2",
            "file_name": "Fedora-Cloud-Base-32-1.6.x86_64.qcow2"
        },
        {
            "name": "Rancher OS Cloud Image",
            "url": "https://github.com/rancher/os/releases/download/v1.5.5/rancheros-openstack.img",
            "file_name": "rancheros-openstack.img"
        },
    ]

    while True:

        for key, distro in enumerate(distro_list):
            print("%s) %s" % (key + 1, distro['name']))

        distro = input("#? ")

        if not distro.isnumeric():
            print("Incorrect Input Selected")
            pass
        elif distro:
            try:
                return distro_list[int(distro) - 1]
            except(IndexError):
                print("Incorrect Input Selected")
        else:
            pass


def download_distro(configs: dict):
    output = "%s/%s" % (configs['iso_storage'], configs['distro']['file_name'])

    print("Output %s" % output)

    class DownloadProgressBar(tqdm):
        def update_to(self, b=1, bsize=1, tsize=None):
            if tsize is not None:
                self.total = tsize
            self.update(b * bsize - self.n)

    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=configs['distro']['url'].split('/')[-1]) as t:
        urllib.request.urlretrieve(configs['distro']['url'], filename=output, reporthook=t.update_to)

    return output


def create_yaml(configs: dict):
    qemu_agent = ""
    restart_qemu_agent = ""

    if configs['install_qemu_agent']:
        qemu_agent = "- qemu-guest-agent"
        restart_qemu_agent = "- systemctl restart qemu-guest-agent"

    content = """
#cloud-config
hostname: %s
manage_etc_hosts: true
user: %s
password: %s
ssh_authorized_keys:
  - %s
chpasswd:
  expire: False
ssh_pwauth: %s
users:
  - default
package_upgrade: true
packages:
 %s
runcmd:
 %s
""" % (
        configs['hostname'],
        configs['username'],
        configs['password'],
        configs['ssh_key'],
        configs['enable_password'],
        qemu_agent,
        restart_qemu_agent
    )

    path = "{path}/{vm_id:n}.yaml".format(path=configs['snippet_storage_path'], vm_id=configs['vm_id'])

    print("Snippet saved in %s" % path)

    with open(path, 'w') as f:
        f.writelines(content)

    return path


def create_cloud_init(configs: dict):
    command = "qm create {vm_id} --name {name} --cores {cores} --onboot 1 --memory {memory} --agent 1,fstrim_cloned_disks=1".format(
        vm_id=configs['vm_id'],
        name=configs['hostname'],
        cores=configs['cpu_cores'],
        memory=configs['ram_memory']
    )
    run_command_with_out_output(command)
    print(command)

    if configs['vlan']:
        command = "qm set {vm_id} --net0 virtio,bridge={network},tag={vlan}".format(
            vm_id=configs['vm_id'],
            network=configs['network_device'],
            vlan=configs['vlan']
        )
        run_command_with_out_output(command)
        print(command)
    else:
        command = "qm set {vm_id} --net0 virtio,bridge={network}".format(
            vm_id=configs['vm_id'],
            network=configs['network_device']
        )
        run_command_with_out_output(command)
        print(command)

    if '.qcow2' in configs['distro']['file_name']:
        command = "qm importdisk {vm_id} {distro_path} {storage} -format qcow2".format(
            vm_id=configs['vm_id'],
            distro_path=configs['distro_path'],
            storage=configs['storage']
        )
        run_command_with_out_output(command)
        print(command)
    else:
        command = "qm importdisk {vm_id} {distro_path} {storage}".format(
            vm_id=configs['vm_id'],
            distro_path=configs['distro_path'],
            storage=configs['storage']
        )
        run_command_with_out_output(command)
        print(command)

    command = "qm set {vm_id} --scsihw virtio-scsi-pci --scsi0 {storage}:vm-{vm_id}-disk-0,discard=on".format(
        vm_id=configs['vm_id'],
        storage=configs['storage']
    )
    run_command_with_out_output(command)
    print(command)

    command = "qm set {vm_id} --ide2 {storage}:cloudinit".format(
        vm_id=configs['vm_id'],
        storage=configs['storage']
    )
    run_command_with_out_output(command)
    print(command)

    command = "qm set {vm_id} --boot c --bootdisk scsi0".format(
        vm_id=configs['vm_id']
    )
    run_command_with_out_output(command)
    print(command)

    command = "qm set {vm_id} --serial0 socket --vga serial0".format(
        vm_id=configs['vm_id']
    )
    run_command_with_out_output(command)
    print(command)

    if configs['network_ip'] == 'dhcp':
        command = "qm set {vm_id} --ipconfig0 ip=dhcp".format(
            vm_id=configs['vm_id']
        )
        run_command_with_out_output(command)
        print(command)
    else:
        command = "qm set {vm_id} --ipconfig0 ip={ip},gw={gateway}".format(
            vm_id=configs['vm_id'],
            ip=configs['network_ip'],
            gateway=configs['network_gateway']
        )
        run_command_with_out_output(command)
        print(command)

    command = "qm set {vm_id} --protection 0".format(
        vm_id=configs['vm_id']
    )
    run_command_with_out_output(command)
    print(command)

    command = "qm set {vm_id} --tablet 0".format(
        vm_id=configs['vm_id']
    )
    run_command_with_out_output(command)
    print(command)

    command = "qm set {vm_id} --cicustom user={snippet_storage}:snippets/{vm_id}.yaml".format(
        vm_id=configs['vm_id'],
        snippet_storage=configs['snippet_storage']
    )
    run_command_with_out_output(command)
    print(command)


def main():
    configs = dict()
    configs['hostname'] = input("\nEnter desired hostname for the Virutal Machine: ")
    configs['vm_id'] = get_vmid()
    configs['username'] = input("\nEnter desired VM username: ")
    configs['password'] = get_password()
    configs['storage'] = get_storage()
    configs['iso_storage'] = get_iso_storage()
    configs['snippet_storage_path'] = get_snippets_storage()
    configs['snippet_storage'] = get_storage()
    print("\nThe snippet storage path of the user.yaml file will be %s" % configs['snippet_storage_path'])
    print("The storage for snippets being used is %s \n\n" % configs['snippet_storage'])
    configs['network_device'] = get_network()
    configs['vlan'] = get_vlan()
    configs['network_ip'], configs['network_gateway'] = get_network_config()
    configs['disk_size'] = get_disk_size()
    configs['ram_memory'] = get_ram()
    configs['cpu_cores'] = get_cpu_cores()
    configs['ssh_key'] = get_ssh_key()
    configs['enable_password'] = enable_password_authenticator()
    configs['install_qemu_agent'] = install_qemu_gust_agent()
    configs['distro'] = get_distros()
    configs['distro_path'] = download_distro(configs)
    configs['snippet_file'] = create_yaml(configs)
    create_cloud_init(configs)
    print("Cloud init criado com sucesso")


main()
