# ����ʱ��: 2021/3/3 17:25
# @File : my_monitor_13.py
# @software : PyCharm
from operator import attrgetter
 
from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
 
 
class MyMonitor13(simple_switch_13.SimpleSwitch13):
 
    def __init__(self, *args, **kwargs):          #��ʼ������
        super(MyMonitor13, self).__init__(*args, **kwargs)
        self.datapaths = {}          #��ʼ����Ա�����������洢����
        self.monitor_thread = hub.spawn(self._monitor)    #��Э�̷���ִ��_monitor���������������������Ա�����Э��ִ�С� hub.spawn()����Э��
 
    """
    Controller�����Ҫ��OpenFlowController��Datapath���๹�ɣ����У�OpenFlowController���������Ryu���ӵ�OpenFlow�����е��¼���
    һ�����¼��������ᴴ��һ��Datapath������������Ը��¼������Ӻ����ݣ�������Щ�¼������ݷ�����н�������װ��Ryu���¼�����Ȼ���ɷ���
    """
    #get datapath info ��ȡdatapath��Ϣ
    #EventOFPStateChange�¼����ڼ�����ӺͶϿ���
    @set_ev_cls(ofp_event.EventOFPStateChange,[MAIN_DISPATCHER,DEAD_DISPATCHER])#ͨ��ryu.controller.handler.set_ev_clsװ������decorator������ע�ᣬ������ʱ��ryu����������֪��MyMonitor13���ģ��ĺ���_state_change_handler������һ���¼�
    def _state_change_handler(self,event):  #������״̬�����仯���ÿ����������ڽ�����һ��
        datapath=event.datapath
        if event.state == MAIN_DISPATCHER:            # ��MAIN_DISPATCHER״̬�£���������������״̬
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x',datapath.id)
                self.datapaths[datapath.id]=datapath   #datapath���ֵ������棬keyΪid,valueΪdatapath
        elif event.state == DEAD_DISPATCHER:          #��DEAD_DISPATCHER״̬��
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath��%016x',datapath.id)
                del self.datapaths[datapath.id]
 
    #send request msg periodically
    def _monitor(self):
        while True:              #����ע�ύ��������ͳ����Ϣ��ȡ����ÿ10�����޵��ظ�һ��
            for dp in self.datapaths.values():  #�������еĽ�����������
                self._request_stats(dp)
            hub.sleep(10)         #����
 
 
    #send stats request msg to datapath        ����ɿ����������·��߼���
    def _request_stats(self,datapath):
        self.logger.debug('send stats request��%016x',datapath.id)
        ofproto=datapath.ofproto
        ofp_parser=datapath.ofproto_parser   #������
 
        # send flow stats request msg
        request=ofp_parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(request)
 
        # send port stats request msg
        request=ofp_parser.OFPPortStatsRequest(datapath,0,ofproto.OFPP_ANY)
        datapath.send_msg(request)
 
 
    #handle the port stats reply msg             ����ɽ��������������߼���
    @set_ev_cls(ofp_event.EventOFPPortStatsReply,MAIN_DISPATCHER)
    def _port_stats_reply_handler(self,event):
        body=event.msg.body     #��Ϣ��
 
        self.logger.info('datapath         port      '
                         'rx-pkts  rx-bytes rx-error '  
                         'tx-pkts  tx-bytes tx-error ')     # rx-pkts:receive packets tx-pks:transmit packets
        self.logger.info('---------------- -------- '
                         '-------- -------- -------- '
                         '-------- -------- --------')
        for stat in sorted(body,key=attrgetter('port_no')):     #attrgetter�����Ի�ȡ����
            self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
                             event.msg.datapath.id, stat.port_no,
                             stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)
 
    #handle the flow entry stats reply msg
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply,MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self,event):
        body=event.msg.body    # body:OFPFlowStats���б����洢��FlowStatsRequestӰ��ÿ���������ͳ����Ϣ
 
        self.logger.info('datapath         '
                         'in-port  eth-dst           '
                         'out-port packets  bytes')
        self.logger.info('---------------- '
                         '-------- ----------------- '
                         '-------- -------- --------')
        for stat in sorted([flow for flow in body if flow.priority==1]
                              ,key=lambda flow:(flow.match['in_port'],flow.match['eth_dst'])):
            self.logger.info('%016x %8x %17s %8x %8d %8d',
                             event.msg.datapath.id,stat.match['in_port'],
                             stat.match['eth_dst'],stat.instructions[0].actions[0].port,
                             stat.packet_count,stat.byte_count)
 
 
 


