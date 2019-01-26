﻿#! /usr/bin/python# encoding:utf-8import paramikoimport osimport timefrom datetime import datetimeimport base64import tools as toolsimport commandsimport cx_Oracleimport codecsimport sysreload(sys)sys.setdefaultencoding('utf-8')# 执行命令,def exec_command(host,user,password,command):    list = []    try:        ssh_client = paramiko.SSHClient()        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())        ssh_client.connect(host, 22, user, password)        std_in, std_out, std_err = ssh_client.exec_command(command)        for line in std_out:            list.append(line.strip("\n"))        ssh_client.close()        return list    except Exception, e:        print e# 上传文件def sftp_upload_file(host,user,password,server_path, local_path):    try:        t = paramiko.Transport((host, 22))        t.connect(username=user, password=password)        sftp = paramiko.SFTPClient.from_transport(t)        sftp.put(local_path, server_path)        t.close()    except Exception, e:        print e#批量上传def sftp_upload_dir(host,user,password,remote_dir,local_dir):    try:        t = paramiko.Transport((host, 22))        t.connect(username=user, password=password)        sftp = paramiko.SFTPClient.from_transport(t)        for root,dirs,files in os.walk(local_dir):            print root,dirs,files            # remote_path = remote_dir + '/' + dirs            for filespatch in files:                local_file = os.path.join(root,filespatch)                a = local_file.replace(local_dir,'')                remote_file = remote_dir +'/' + local_file.replace("\\", "/")                sftp.put(local_file, remote_file)                print '成功上传：%s 到 %s' %(local_file,remote_file)    except Exception,e:        print e# oracle数据库安装def oracle_install(host,user,password):    log_type = 'Oracle部署'    tools.mysql_exec("delete from many_logs where log_type = 'Oracle部署'",'')    # 清除目标目录    cmd = 'rm -rf /tmp/oracle_install'    exec_command(host, user, password, cmd)    # 创建文件目录    cmd = 'mkdir -p /tmp/oracle_install/oracle_rpms/centos6'    exec_command(host, user, password, cmd)    # 上传安装部署文件    sftp_upload_dir(host,user,password,'/tmp','oracle_install')    tools.my_log(log_type, '预上传文件完成！','')    #1. 安装rpm包    cmd = 'sh /tmp/oracle_install/1_ora_yum.sh > /tmp/oracle_install/1_ora_yum.log'    exec_command(host, user, password, cmd)    tools.my_log(log_type, '执行1_ora_yum.sh，rpm包安装完成！','')    #2.环境初始化，建组、用户，配置资源限制，内核参数    cmd = 'sh /tmp/oracle_install/2_ora_init.sh > /tmp/oracle_install/2_ora_init.log'    exec_command(host, user, password, cmd)    tools.my_log(log_type, '执行2_ora_init.sh，环境初始化完成！','')    #3. 创建目录    cmd = 'sh /tmp/oracle_install/3_fd_init.sh > /tmp/oracle_install/3_fd_init.log'    exec_command(host, user, password, cmd)    tools.my_log(log_type, '执行3_fd_init.sh，目录创建完成！','')    #4. 配置Oracle用户环境变量    cmd = 'sh /tmp/oracle_install/4_ora_profile.sh > /tmp/oracle_install/4_ora_profile.log'    exec_command(host, user, password, cmd)    tools.my_log(log_type, '执行4_ora_profile.sh，Oracle用户环境变量配置完成！','')    #5. 上传安装包和安装文件    cmd = 'sh /tmp/oracle_install/5_init_orahome.sh > /tmp/oracle_install/5_init_orahome.log'    exec_command(host, user, password, cmd)    tools.my_log(log_type, '执行5_init_orahome.sh，Oracle安装文件传输完成！', '')# Oracle数据库启停def oracle_shutdown(host,user,password):    log_type = '关闭Oracle数据库'    tools.mysql_exec("delete from many_logs where log_type = '关闭Oracle数据库'", '')    # 上传脚本    local_file = os.getcwd() + '/frame/oracle_tools/ora_shutdown.sh'    print local_file    sftp_upload_file(host,user,password,'/tmp/ora_shutdown.sh',local_file)    # 执行命令    cmd = 'sh /tmp/ora_shutdown.sh > /tmp/ora_shutdown.log'    exec_command(host,user,password,cmd)    tools.my_log(log_type, '执行ora_shutdown.sh，Oracle数据库关闭成功！', '')# Oracle数据库启停def oracle_startup(host,user,password):    log_type = '启动Oracle数据库'    tools.mysql_exec("delete from many_logs where log_type = '启动Oracle数据库'", '')    # 上传脚本    local_file = os.getcwd() + '/frame/oracle_tools/ora_startup.sh'    print local_file    sftp_upload_file(host,user,password,'/tmp/ora_startup.sh',local_file)    # 执行命令    cmd = 'sh /tmp/ora_startup.sh > /tmp/ora_startup.log'    exec_command(host,user,password,cmd)    tools.my_log(log_type, 'ora_startup.sh，Oracle数据库启动成功！', '')def oracle_exec_sql():    log_type = 'Oracle执行sql脚本'    local_dir = os.getcwd()    cmd = 'ls %s/frame/sqlscripts/*.sql' %local_dir    status, result = commands.getstatusoutput(cmd)    if status == 0:        sql_list = result.split('\n')        for sql in sql_list:            print '开始执行脚本：%s' %sql            sql_name = sql.split('/')[-1]            sql_no = sql_name.split('_')[0]            user = 'dbmon'            password = 'oracle'            tnsname = sql.split('_')[1]            cmd = 'sqlplus -s %s/%s@%s @%s' %(user,password,tnsname,sql)            status, result = commands.getstatusoutput(cmd)            if status == 0 and not 'ORA-' in result :                print result                print '%s执行成功！'%sql                tools.my_log(log_type, '%s执行成功！' %sql, '')                tools.my_log(log_type, '执行信息：%s' % result, '')                cmd = 'rm %s' %sql                status, result = commands.getstatusoutput(cmd)                print '%s脚本已删除！' %sql                tools.my_log(log_type, '%s脚本已删除！' % sql, '')                sql = "update sql_list set result = '成功',result_color = 'green' where sql_no=%s" %sql_no                tools.mysql_exec(sql,'')            else:                print result                print '%s执行失败，已回滚！' %sql                tools.my_log(log_type, '%s执行失败，已回滚！' % sql, '')                tools.my_log(log_type,'','异常信息：%s' % result)                cmd = 'rm %s' %sql                status, result = commands.getstatusoutput(cmd)                print '%s脚本已删除！' %sql                tools.my_log(log_type, '%s脚本已删除！' % sql, '')                sql = "update sql_list set result = '失败',result_color = 'red' where sql_no=%s" % sql_no                tools.mysql_exec(sql, '')def get_oracle_para(url,username,password,para):    sql = "select a.name,a.VALUE,a.DESCRIPTION from v$parameter a where a.name='%s' " %para    oracle_para = tools.ora_qry(url,username,password,sql)    para_value = oracle_para[0][1]    para_description = oracle_para[0][2]    return para_valuedef oracle_switchover(p_host,p_user,p_password,s_host,s_user,s_password):    log_type = 'Oracle容灾切换'    tools.mysql_exec("delete from many_logs where log_type = 'Oracle容灾切换'", '')    # 上传脚本    local_file = os.getcwd() + '/frame/oracle_tools/switchover/switchOverForPrimary.sh'    sftp_upload_file(p_host, p_user, p_password, '/tmp/switchOverForPrimary.sh', local_file)    # 执行命令 主转备    cmd = 'sh /tmp/switchOverForPrimary.sh > /tmp/switchOverForPrimary.log'    exec_command(p_host, p_user, p_password, cmd)    tools.my_log(log_type, 'ssh to %s：执行switchOverForPrimary.sh，主库切换为备库成功！' %p_host, '')    # 上传脚本    local_file = os.getcwd() + '/frame/oracle_tools/switchover/startupPrimary.sh'    sftp_upload_file(p_host, p_user, p_password, '/tmp/startupPrimary.sh', local_file)    # 执行命令 开启主库    cmd = 'sh /tmp/startupPrimary.sh > /tmp/startupPrimary.log'    exec_command(p_host, p_user, p_password, cmd)    tools.my_log(log_type, 'ssh to %s：执行startupPrimary.sh，主库启动成功！' %p_host, '')    # 上传脚本    local_file = os.getcwd() + '/frame/oracle_tools/switchover/switchOverForStandby.sh'    sftp_upload_file(s_host, s_user, s_password, '/tmp/switchOverForStandby.sh', local_file)    # 执行命令 备转主    cmd = 'sh /tmp/switchOverForStandby.sh > /tmp/switchOverForStandby.log'    print cmd    exec_command(s_host, s_user, s_password, cmd)    tools.my_log(log_type, 'ssh to %s：执行switchOverForStandby.sh，备库切换为主库成功！' %s_host, '')def get_report(tags,url,user,password,report_type,begin_snap,end_snap):    # 获取报告相关信息    sql = "select instance_number from v$instance"    res = tools.oracle_query(url,user,password,sql)    instance_num = res[0][0]    sql = "select dbid from v$database"    res = tools.oracle_query(url,user,password,sql)    dbid = res[0][0]    sql = "select instance_name from v$instance"    res = tools.oracle_query(url, user, password, sql)    instance_name = res[0][0]    if report_type == 'ash':        report_begin_time = begin_snap        report_end_time = end_snap    else:        sql = "select to_char(a.end_interval_time,'yyyy-mm-dd hh24:mi:ss') from dba_hist_snapshot a where a.snap_id=%s" % begin_snap        res = tools.oracle_query(url, user, password, sql)        report_begin_time = res[0][0]        sql = "select to_char(a.end_interval_time,'yyyy-mm-dd hh24:mi:ss') from dba_hist_snapshot a where a.snap_id=%s" % end_snap        res = tools.oracle_query(url, user, password, sql)        report_end_time = res[0][0]    # 生成报告    if report_type == 'awr':        data = get_awr(url, user, password, dbid, instance_num, begin_snap, end_snap)    elif report_type == 'addm':        data = get_addm(url, user, password, instance_name,dbid, instance_num, begin_snap, end_snap)    else:        data = get_ash(url, user, password,dbid, instance_num, begin_snap, end_snap)    if report_type == 'addm':        suffix = 'txt'    else:        suffix = 'html'    if report_type =='ash':        now = time.strftime('%H%M%S')        report_path = 'oracle_report/%s_%s_%s_%s.%s' % (        report_type, dbid, instance_num,now,suffix)    else:        report_path = 'oracle_report/%s_%s_%s_%s_%s.%s' % (        report_type, dbid, instance_num, begin_snap, end_snap, suffix)    local_path = os.getcwd()+ '/templates/' + report_path    save_report(local_path,data)    insert_sql = " INSERT INTO oracle_report(tags,report_begin_time,report_end_time,report_type,report_path,status) values('%s','%s','%s','%s','%s','已生成') " %(tags,report_begin_time,report_end_time,report_type,report_path)    tools.mysql_exec(insert_sql,'')def get_awr(url,user,password,dbid,instance_num,begin_snap,end_snap):    dbconn = cx_Oracle.connect(user, password, url)    sql = """            select output from table(                dbms_workload_repository.awr_report_html(                    :dbid,                    :inst_num,                    :bid,                    :eid,                0))        """    cur = dbconn.cursor()    cur.execute(sql, (dbid, instance_num, begin_snap, end_snap))    res = cur.fetchall()    return resdef get_addm(url,user,password,instance_name,dbid,instance_num,begin_snap,end_snap):    dbconn = cx_Oracle.connect(user, password, url)    desc = 'ADDM run: snapshots [ %s, %s ], instance %s, database id %s' % (        begin_snap, end_snap, instance_name, dbid)    sql_create_task = """begin            dbms_advisor.create_task('ADDM', :id, :name, :descr, null);            dbms_advisor.set_task_parameter(:name, 'START_SNAPSHOT', :bid);            dbms_advisor.set_task_parameter(:name, 'END_SNAPSHOT', :eid);            dbms_advisor.set_task_parameter(:name, 'INSTANCE', :inst_num);            dbms_advisor.set_task_parameter(:name, 'DB_ID', :dbid);            dbms_advisor.execute_task(:name);            end;        """    cur = dbconn.cursor()    id = cur.var(cx_Oracle.NUMBER)    name = cur.var(cx_Oracle.STRING)    cur.execute(sql_create_task, {        'id': id,        'name': name,        'descr': desc,        'bid': begin_snap,        'eid': end_snap,        'inst_num': instance_num,        'dbid': dbid})    sql_get_report = "select dbms_advisor.get_task_report(:task_name, 'TEXT', 'TYPICAL') from sys.dual"    cur.execute(sql_get_report, {'task_name': name.getvalue()})    ret, = cur.fetchone()    return [(ret.read(),)]def get_ash(url,user,password,dbid,instance_num,begin_snap,end_snap):    dbconn = cx_Oracle.connect(user, password, url)    sql = """select output from table (                    DBMS_WORKLOAD_REPOSITORY.ASH_REPORT_HTML(                    :db_id,                    :inst_num,                    :start_time,                    :end_time                 ))            """    cur = dbconn.cursor()    start_time = datetime.strptime(begin_snap, '%Y-%m-%d %H:%M')    end_time = datetime.strptime(end_snap, '%Y-%m-%d %H:%M')    cur.execute(sql, (dbid, instance_num, start_time, end_time))    res = cur.fetchall()    return resdef save_report(filename,data):    with codecs.open(filename, 'w','utf-8') as f:        for l in data:            if l is not None and l[0] is not None:                content =  l[0].decode("gbk").encode("utf-8")                f.write(content + '\n')def oracle_logmnr(url,user,password,schema,object,operation,log_list):    # 获取目标解析文件    conn = cx_Oracle.connect(user, password, url)    cursor = conn.cursor()    # 将选中的日志加到分析范围    for idx, i in enumerate(log_list):        logfile = i['logfile']        print logfile        if idx == 0:            sql = """                     begin                     dbms_logmnr.add_logfile(:logfile,dbms_logmnr.new);                     end;                     """        else:            sql = """                      begin                      dbms_logmnr.add_logfile(:logfile,dbms_logmnr.addfile);                      end;                      """        cursor.execute(sql, {'logfile': logfile})    # 启动logminer    dict = '/u01/app/logminer/dictionary.ora'    sql = """             begin             dbms_logmnr.start_logmnr(0,0,null,null,:dict,0);             end;             """    cursor.execute(sql, {'dict': dict})    # 清空    sql = "delete from logmnr_contents"    cursor.execute(sql)    # 存储结果    sql = "insert into logmnr_contents select rownum id,a.* from v$logmnr_contents a where seg_owner like nvl(upper('%s'),seg_owner) " \          "and seg_name like nvl(upper('%s'),seg_name) and operation like nvl('%s',operation) and seg_owner<>'SYS' " % (          schema, object, operation)    cursor.execute(sql)    conn.commit()    # 关闭游标    cursor.close()    conn.close()if __name__ == '__main__':    url = '192.168.48.10:1521/orcl'    username = 'dbmon'    password = 'oracle'    report_type = 'addm'    get_report(url,username,password,report_type,2675,2677)