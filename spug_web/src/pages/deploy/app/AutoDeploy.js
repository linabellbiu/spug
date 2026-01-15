import React, { useState, useEffect } from 'react';
import { observer } from 'mobx-react';
import { Modal, Form, Alert, message } from 'antd';
import { http } from 'libs';
import store from './store';
import styles from './index.module.css';


export default observer(function AutoDeploy() {
  const [url, setURL] = useState();
  const [key, setKey] = useState();

  useEffect(() => {
    http.post('/api/app/kit/key/', {key: 'api_key'})
      .then(res => setKey(res))
    
    const prefix = window.location.origin;
    setURL(`${prefix}/api/apis/deploy/${store.deploy.id}/`)
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

  return (
    <Modal
      visible
      width={540}
      title="Webhook"
      footer={null}
      onCancel={() => store.autoVisible = false}>
      <Alert showIcon type="info" style={{width: 440, margin: '0 auto 24px'}} message="Webhook可以用来与Git结合实现触发后自动发布。"/>
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
      </Form>
    </Modal>
  )
})