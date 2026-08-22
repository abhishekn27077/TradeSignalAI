import React, { useEffect } from 'react';
import { Card } from '../components/core/Card';
import { Badge } from '../components/core/Badge';
import { KPICard } from '../components/core/KPICard';
import { Clock, Server, ArrowRightLeft, CheckCircle2, XCircle, RefreshCw } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api-client';

export const ExecutionPage: React.FC = () => {
  const storeOrders = useAppStore((s) => s.orders);
  const refreshOrders = useAppStore((s) => s.refreshOrders);
  const [brokerHealth, setBrokerHealth] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await refreshOrders();
      try {
        const stat = await api.brokers.status();
        setBrokerHealth(stat);
      } catch {}
      setLoading(false);
    };
    load();
    const interval = setInterval(refreshOrders, 10000);
    return () => clearInterval(interval);
  }, []);

  const displayOrders = storeOrders;
  const filled = displayOrders.filter((o: any) => o.status === 'FILLED' || o.status === 'filled').length;
  const pending = displayOrders.filter((o: any) => o.status === 'PENDING' || o.status === 'SUBMITTED' || o.status === 'pending').length;
  const rejected = displayOrders.filter((o: any) => o.status === 'REJECTED' || o.status === 'rejected').length;

  return (
    <div className="h-full flex flex-col gap-3 p-3 overflow-hidden bg-trading-dark">
      <div className="flex items-center justify-between shrink-0">
        <h2 className="text-sm font-semibold text-text-primary">Execution Dashboard</h2>
        <button onClick={() => { refreshOrders(); }} className="p-1 text-text-muted hover:text-text-primary"><RefreshCw className="w-3.5 h-3.5" /></button>
      </div>

      <div className="grid grid-cols-4 gap-3 shrink-0">
        <KPICard label="Filled Orders" value={filled.toString()} icon={<CheckCircle2 className="w-4 h-4 text-profit" />} />
        <KPICard label="Pending Queue" value={pending.toString()} icon={<Clock className="w-4 h-4 text-warning" />} />
        <KPICard label="Rejected" value={rejected.toString()} icon={<XCircle className="w-4 h-4 text-loss" />} />
        <KPICard label="Total Orders" value={displayOrders.length.toString()} icon={<ArrowRightLeft className="w-4 h-4 text-text-secondary" />} />
      </div>

      <div className="flex-1 grid grid-cols-[1fr_350px] gap-3 min-h-0">
        <Card title="Order Execution Log" noPadding className="flex flex-col h-full overflow-hidden">
          <div className="flex-1 overflow-auto">
            {loading && displayOrders.length === 0 ? (
              <div className="flex items-center justify-center h-32 text-text-muted text-xs">Loading orders...</div>
            ) : displayOrders.length === 0 ? (
              <div className="flex items-center justify-center h-32 text-text-muted text-xs">No orders executed yet</div>
            ) : (
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-trading-surface z-10">
                  <tr className="text-text-muted text-[10px] uppercase tracking-wider border-b border-panel-border">
                    <th className="text-left px-4 py-2.5 font-medium">Order ID</th>
                    <th className="text-left px-4 py-2.5 font-medium">Symbol</th>
                    <th className="text-center px-4 py-2.5 font-medium">Side</th>
                    <th className="text-right px-4 py-2.5 font-medium">Qty</th>
                    <th className="text-right px-4 py-2.5 font-medium">Price</th>
                    <th className="text-center px-4 py-2.5 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {displayOrders.map((ord: any) => (
                    <tr key={ord.id} className="border-b border-panel-border/30 hover:bg-trading-hover transition-colors">
                      <td className="px-4 py-2 font-mono text-text-secondary whitespace-nowrap">{ord.id?.toString().slice(0, 12)}</td>
                      <td className="px-4 py-2 font-medium text-text-primary whitespace-nowrap">{ord.symbol}</td>
                      <td className="px-4 py-2 text-center whitespace-nowrap">
                        <Badge variant={ord.direction === 'BUY' ? 'profit' : 'loss'}>{ord.direction}</Badge>
                      </td>
                      <td className="px-4 py-2 text-right font-mono text-text-secondary whitespace-nowrap">{ord.quantity || ord.qty}</td>
                      <td className="px-4 py-2 text-right font-mono text-text-primary whitespace-nowrap">
                        {ord.price?.toLocaleString() || ord.filledPrice?.toLocaleString() || '--'}
                      </td>
                      <td className="px-4 py-2 text-center whitespace-nowrap">
                        <div className="flex items-center justify-center gap-1.5">
                          {(ord.status === 'FILLED' || ord.status === 'filled') && <CheckCircle2 className="w-3.5 h-3.5 text-profit" />}
                          {(ord.status === 'REJECTED' || ord.status === 'rejected') && <XCircle className="w-3.5 h-3.5 text-loss" />}
                          {(ord.status === 'PENDING' || ord.status === 'SUBMITTED' || ord.status === 'pending') && <Clock className="w-3.5 h-3.5 text-warning" />}
                          <span className={`text-[11px] ${
                            ord.status === 'FILLED' || ord.status === 'filled' ? 'text-profit' :
                            ord.status === 'REJECTED' || ord.status === 'rejected' ? 'text-loss' : 'text-warning'
                          }`}>{ord.status}</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Card>

        <div className="flex flex-col gap-3">
          <Card title="Broker Gateway Status">
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between p-3 bg-trading-surface border border-panel-border rounded-lg">
                <div className="flex items-center gap-3">
                  <Server className="w-5 h-5" />
                  <div>
                    <div className="text-sm font-medium text-text-primary">MetaTrader 5</div>
                    <div className="text-[10px] text-text-muted">{brokerHealth ? 'Backend Connected' : 'No Connection'}</div>
                  </div>
                </div>
                <Badge variant={brokerHealth ? 'profit' : 'loss'} dot>{brokerHealth ? 'ACTIVE' : 'OFFLINE'}</Badge>
              </div>
            </div>
          </Card>

          <Card title="Execution Diagnostics" className="flex-1">
            <div className="text-[11px] text-text-secondary space-y-2">
              <div className="flex justify-between"><span className="text-text-muted">Total Orders</span><span data-mono>{displayOrders.length}</span></div>
              <div className="flex justify-between"><span className="text-text-muted">Filled</span><span data-mono className="text-profit">{filled}</span></div>
              <div className="flex justify-between"><span className="text-text-muted">Pending</span><span data-mono className="text-warning">{pending}</span></div>
              <div className="flex justify-between"><span className="text-text-muted">Rejected</span><span data-mono className="text-loss">{rejected}</span></div>
              <div className="flex justify-between"><span className="text-text-muted">Broker Connected</span><span data-mono className={brokerHealth ? 'text-profit' : 'text-loss'}>{brokerHealth ? 'Yes' : 'No'}</span></div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};