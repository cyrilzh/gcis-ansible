import csv
import os
import argparse

legacy_name = "Original VM Name *"
new_name = "New VM Name"
pnat_ip = "PNAT IP"
pnat_port = "PNAT Port"
new_IP = "Virtual Machine IP"
ssh_port = "22"
batch = "Batch"
target_env = "Environment"


def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


def mode_arg(string):
    result = string.lower()
    if result in ('a', 'i', 'h'):
        return result
    else:
        raise ValueError(
            'Mode参数错误: Mode参数需要设置为"a", "i" or "h"中的一个。')


def env_arg(string):
    result = string.lower()
    if result in ('p1', 'p2'):
        return result
    else:
        raise ValueError(
            'Env参数错误: ENV参数需要设置为"p1" or "p2"中的一个。')


def batch_arg(string):
    result = string.upper()
    if result in ("", '2', '3', '3A', '4', '5', '6', '7', '8', '9', '10'):
        return result
    else:
        raise ValueError(
            'Batch参数错误: Batch参数需要设置为2~10中的数字，或3A。')


def network_arg(string):
    result = string.lower()
    if result in ('vpn', 'intranet'):
        return result
    else:
        raise ValueError(
            'Network参数错误：Network参数需要设置为VPN或Intranet.')


def file_path(string):
    if os.path.isfile(string):
        return string
    else:
        raise FileNotFoundError(string)


def match_batch(row_batch, args_batch):
    if args_batch == "":
        return True
    else:
        return row_batch == "Batch "+args_batch


# generate_hostvar 用于生成host_var目录下的文件
def generate_hostvar(args):
    output_path = os.path.join(
        args.path, args.environment+"_"+args.network, args.batch, 'host_vars')
    os.makedirs(output_path, exist_ok=True)
    with open(args.log) as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=',')
        for row in csvreader:
            if row[target_env].lower() == args.environment.lower() and match_batch(row[batch], args.batch):
                with open(os.path.join(output_path, row[new_name]), 'w') as f:
                    f.write('legacyName: "'+str.strip(row[legacy_name])+'"\n')
                    f.write('newName: "'+str.strip(row[new_name])+'"\n')
                    f.write('newIP: "'+str.strip(row[new_IP])+'"\n')
    return

# generate_inventory_file 用于生成yml格式的inventory文件，包括Ansible IP和端口。
# 所生成的文件只有一个Linux组


def generate_inventory_file(args):
    output_path = os.path.join(
        args.path, args.environment+"_"+args.network, args.batch)
    os.makedirs(output_path, exist_ok=True)
    matched_vm_count = 0
    with open(args.log) as csvfile, open(os.path.join(output_path, args.inventory), 'w') as f:
        csvreader = csv.DictReader(csvfile, delimiter=',')
        f.write('all:\n'+' '*2+'hosts:\n'+' '*2+'children:\n' +
                ' '*4+'linux:\n'+' '*6+'hosts:\n')
        for row in csvreader:
            if row[target_env].lower() == args.environment.lower() and match_batch(row[batch], args.batch):
                matched_vm_count = matched_vm_count+1
                f.write(' '*8+row[new_name]+':\n')
                if args.network == "intranet":
                    f.write(' '*10+'ansible_host: '+row[new_IP]+'\n')
                    f.write(' '*10+'ansible_port: 22\n')
                else:
                    f.write(' '*10+'ansible_host: '+row[pnat_ip]+'\n')
                    f.write(' '*10+'ansible_port: '+row[pnat_port]+'\n')
                f.write(' '*10+'ansible_user: pa_eidsvc\n')
    print("共处理了%d个VM" % (matched_vm_count))
    return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s 1.0.1')
    parser.add_argument(
        '-l',
        '--log',
        help='指定需要导入的csv文件路径，工具将根据此文件生成Ansible Inventory的host_vars和Inventory文件。csv文件从Migration Request Form的IaaS Request标签页中导出。',
        required=True,
        type=file_path)
    parser.add_argument(
        '-m',
        '--mode',
        help='指定产生的Ansible Inventory数据种类，H代表仅产生host_var数据；I代表仅产生包含Ansible需要访问的IP和端口的Inventory文件；A为默认选项，代表同时开启H和I。',
        type=mode_arg,
        default='a')
    parser.add_argument(
        '-p',
        '--path',
        help='指定输出文件的保存路径，默认为当前路径。',
        type=dir_path,
        default=".")
    parser.add_argument(
        '-i',
        '--inventory',
        help='指定Inventory文件的名称，默认为hosts.yml。',
        type=str,
        default="hosts.yml")
    parser.add_argument(
        '-e',
        '--environment',
        help='指定所生成的Inventory中的虚拟机属于哪一个机房，P1还是P2。',
        type=env_arg,
        default="p1")
    parser.add_argument(
        '-b',
        '--batch',
        help='指定所生成的Inventory中的虚拟机属于哪一个部署批次，有效值为2到10以及3A。',
        type=batch_arg,
        default="")
    parser.add_argument(
        '-n',
        '--network',
        help='指定Ansible从哪一个网络访问目标虚拟机，VPN还是内网。选择VPN的时候，将使用各虚拟机的PNAT IP和端口。默认选项是Intranet',
        type=network_arg,
        default="Intranet")

    args = parser.parse_args()

    if (args.mode == "a"):
        generate_inventory_file(args)
        generate_hostvar(args)
    elif (args.mode == "i"):
        generate_inventory_file(args)
    elif (args.mode == "h"):
        generate_hostvar(args)


if __name__ == "__main__":
    main()
