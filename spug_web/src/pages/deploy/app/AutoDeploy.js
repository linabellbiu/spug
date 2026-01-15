import React, { useState, useEffect } from 'react';
import { observer } from 'mobx-react';
import { Modal, Form, Alert, message, Input, Button, Space, Select } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { http } from 'libs';
import store from './store';
import envStore from 'pages/config/environment/store';
import styles from './index.module.css';


export default observer(function AutoDeploy() {
  const [url, setURL] = useState();
  const [key, setKey] = useState();
  const [webhookConfig, setWebhookConfig] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    http.post('/api/app/kit/key/', {key: 'api_key'})
      .then(res => setKey(res))
    
    const prefix = window.location.origin;
    setURL(`${prefix}/api/apis/deploy/${store.app_id}/`)
    
    http.get('/api/app/webhook/config/', {params: {app_id: store.app_id}})
      .then(res => setWebhookConfig(res))
  }, [])

  function copyToClipBoard(data) {
    const t = document.createElement('input');
    t.value = data;
    document.body.appendChild(t);
    t.select();
    document.execCommand('copy');
    t.remove();
    message.success('已复制')
  }

  function handleSave() {
    setLoading(true);
    http.post('/api/app/webhook/config/', {app_id: store.app_id, webhook_config: webhookConfig})
      .then(() => {
        message.success('保存成功');
        store.autoVisible = false;
      })
      .finally(() => setLoading(false))
  }

  function handleBranchChange(envId, value) {
    setWebhookConfig({...webhookConfig, [envId]: value});
  }

  const environments = envStore.records || [];
  const appDeploys = store.records[`a${store.app_id}`]?.deploys || [];
  const deployEnvIds = appDeploys.map(d => d.env_id);

  return (
    <Modal
      visible
      width={800}
      title="Webhook 配置"
      onOk={handleSave}
      confirmLoading={loading}
      onCancel={() => store.autoVisible = false}>
      <Alert showIcon type="info" style={{marginBottom: 24}} message="Webhook可以用来与Git结合实现触发后自动发布。配置不同环境的分支匹配规则，当Git推送对应分支时，会自动触发该环境的部署。"/>
      <Form labelCol={{span: 6}} wrapperCol={{span: 16}}>
        <Form.Item label="Webhook URL" extra="点击复制链接，目前支持Gitee、Github、Gitlab、Gogs、Coding和Codeup(阿里云)。支持Branch Push、Tag Push和Merge Request自动触发。">
          <div className={styles.webhook} onClick={() => copyToClipBoard(url)}>{url}</div>
        </Form.Item>
        {key ? (
          <Form.Item
            label="Secret Token"
            tooltip="调用该Webhook接口的访问凭据，在Gitee中为WebHook密码，Gogs中为密钥文本。"
            extra={`点击复制，老版本gitlab等无该项设置的可以在上述Webhook URL后边附加 &token=${key}`}>
            <div className={styles.webhook} onClick={() => copyToClipBoard(key)}>{key}</div>
          </Form.Item>
        ) : (
          <Form.Item label="Secret Token" tooltip="调用该Webhook接口的访问凭据，在Gitee中为WebHook密码，Gogs中为密钥文本。">
            <div style={{color: '#ff4d4f'}}>请在系统管理/系统设置/开放服务设置中设置。</div>
          </Form.Item>
        )}
        <Form.Item 
          label="环境分支配置" 
          extra="配置每个环境对应的分支匹配规则。支持精确匹配、通配符(*)和正则表达式。例如：master、dev、feature/*、^release/.*$">
          <div style={{marginTop: 8}}>
            {appDeploys.map(deploy => {
              const env = environments.find(e => e.id === deploy.env_id);
              if (!env) return null;
              return (
                <div key={deploy.env_id} style={{marginBottom: 12}}>
                  <Space style={{width: '100%'}} align="start">
                    <div style={{width: 120, lineHeight: '32px', textAlign: 'right'}}>
                      {env.name}:
                    </div>
                    <Input
                      style={{flex: 1, width: 400}}
                      placeholder="例如: master 或 dev 或 feature/* 或 ^release/.*$"
                      value={webhookConfig[deploy.env_id] || ''}
                      onChange={e => handleBranchChange(deploy.env_id, e.target.value)}
                    />
                  </Space>
                </div>
              );
            })}
            {appDeploys.length === 0 && (
              <div style={{color: '#999'}}>该应用暂无发布配置，请先创建发布配置。</div>
            )}
          </div>
        </Form.Item>
      </Form>
    </Modal>
  )
})