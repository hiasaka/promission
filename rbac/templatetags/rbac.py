#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re
import os
from django import template
from django.utils.safestring import mark_safe
from django.conf import settings

register = template.Library()


def process_menu_tree_data(request):
    """
    根据Session中获取的菜单以及权限信息，结构化数据，生成特殊数据结构，如：
    [
        {id:1,caption:'菜单标题',parent_id:None,status:False,opened:False,child:[...]},
    ]
    PS: 最后一层的权限会有url，即：菜单跳转的地址
    
    :param request: 
    :return: 
    """
    menu_permission_dict = request.session.get(settings.RBAC_MENU_PERMISSION_SESSION_KEY)
    if not menu_permission_dict:
        raise Exception('Session中未保存当前用户菜单以及权限信息，请登录后初始化权限信息！')

    """ session中获取菜单和权限信息 """
    all_menu_list = menu_permission_dict[settings.RBAC_MENU_KEY]
    menu_permission_list = menu_permission_dict[settings.RBAC_MENU_PERMISSION_KEY]

    all_menu_dict = {}
    for row in all_menu_list:
        row['opened'] = False
        row['status'] = False
        row['child'] = []
        all_menu_dict[row['id']] = row
    '''
    {1: {'child': [], 'parent_id': None, 'caption': '菜单一', 'status': False, 'opened': False, 'id': 1},
    2: {'child': [], 'parent_id': None, 'caption': '菜单二', 'status': False, 'opened': False, 'id': 2},
    3: {'child': [], 'parent_id': None, 'caption': '菜单三', 'status': False, 'opened': False, 'id': 3},
    4: {'child': [], 'parent_id': 1, 'caption': '菜单一杠一', 'status': False, 'opened': False, 'id': 4},
    5: {'child': [], 'parent_id': 2, 'caption': '菜单二杠二', 'status': False, 'opened': False, 'id': 5}}
    '''

    """ 将权限信息挂靠在菜单上，并设置是否默认打开，以及默认显示 """
    for per in menu_permission_list:

        item = {'id': per['permission_id'], 'caption': per['permission__caption'], 'url': per['permission__url'],
                'parent_id': per['permission__menu_id'],
                'opened': False,
                'status': True}
        menu_id = item['parent_id']
        all_menu_dict[menu_id]['child'].append(item)

        # 将当前URL和权限正则进行匹配，用于指示是否默认打开菜单
        if re.match(item['url'], request.path_info):
            item['opened'] = True

        if item['opened']:
            pid = menu_id
            while not all_menu_dict[pid]['opened']:
                all_menu_dict[pid]['opened'] = True
                pid = all_menu_dict[pid]['parent_id']
                if not pid:
                    break

        if item['status']:
            pid = menu_id
            while not all_menu_dict[pid]['status']:
                all_menu_dict[pid]['status'] = True
                pid = all_menu_dict[pid]['parent_id']
                if not pid:
                    break

    '''
    {1: {'parent_id': None, 'status': True, 'child': [{'parent_id': 1, 'status': True, 'id': 5, 'caption': '解决保障', 'url': '/troublekill.html', 'opened': False}], 'id': 1, 'caption': '菜单一', 'opened': False},
    2: {'parent_id': None, 'status': False, 'child': [], 'id': 2, 'caption': '菜单二', 'opened': False},
    3: {'parent_id': None, 'status': True, 'child': [{'parent_id': 3, 'status': True, 'id': 6, 'caption': '报障管理', 'url': '/trouble.html', 'opened': False}], 'id': 3, 'caption': '菜单三', 'opened': False},
    4: {'parent_id': 1, 'status': False, 'child': [], 'id': 4, 'caption': '菜单一杠一', 'opened': False},
    5: {'parent_id': 2, 'status': False, 'child': [], 'id': 5, 'caption': '菜单二杠二', 'opened': False}}


    '''
    result = []
    for row in all_menu_list:
        pid = row['parent_id']
        if pid:
            all_menu_dict[pid]['child'].append(row)
        else:
            result.append(row)

    return result



def build_menu_tree_html(menu_list):
    tpl1 = """
        <div class='rbac-menu-item'>
            <div class='rbac-menu-header'>{0}</div>
            <div class='rbac-menu-body {2}'>{1}</div>
        </div>
    """
    tpl2 = """
        <a href='{0}' class='{1}'>{2}</a>
    """
    menu_str = ""
    for menu in menu_list:
        if not menu['status']:
            continue

        if menu.get('url'):
            menu_str += tpl2.format(menu['url'], "rbac-active" if menu['opened'] else '', menu['caption'])
        else:
            if menu.get('child'):
                child = build_menu_tree_html(menu.get('child'))
            else:
                child = ""
            menu_str += tpl1.format(menu['caption'], child, "" if menu['opened'] else 'rbac-hide')
    return menu_str


@register.simple_tag
def rbac_menu(request):
    """
    根据Session中当前用户的菜单信息以及当前URL生成菜单
    :param request: 请求对象 
    :return: 
    """
    menu_tree_list = process_menu_tree_data(request)
    return mark_safe(build_menu_tree_html(menu_tree_list))


@register.simple_tag
def rbac_css():
    file_path = os.path.join('rbac', 'theme', settings.RBAC_THEME, 'rbac.css')
    if os.path.exists(file_path):
        return mark_safe(open(file_path, 'r', encoding='utf-8').read())
    else:
        raise Exception('rbac主题CSS文件不存在')


@register.simple_tag
def rbac_js():
    file_path = os.path.join('rbac', 'theme', settings.RBAC_THEME, 'rbac.js')
    if os.path.exists(file_path):
        return mark_safe(open(file_path, 'r', encoding='utf-8').read())
    else:
        raise Exception('rbac主题JavaScript文件不存在')
