import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Typography, Tabs, Spin, Table, Tag } from 'antd';
import { BrainCircuit, Activity, Database, TrendingUp, FileText, BarChart2 } from 'lucide-react';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

export const AIResearchDashboard: React.FC = () => {
  const [reports, setReports] = useState<any>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const [daily, weekly, monthly, quarterly] = await Promise.all([
          fetch('/api/v1/validation/reports/daily'),
          fetch('/api/v1/validation/reports/weekly'),
          fetch('/api/v1/validation/reports/monthly'),
          fetch('/api/v1/validation/reports/quarterly')
        ]);
        setReports({
          daily: await daily.json(),
          weekly: await weekly.json(),
          monthly: await monthly.json(),
          quarterly: await quarterly.json()
        });
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);

  const renderReportCard = (period: string) => {
    const report = reports[period];
    if (!report || !report.metrics) return null;
    const { metrics, rankings } = report;

    return (
      <div className="space-y-6">
        <Card title={report.title} className="bg-gray-900 border-gray-700">
          <Text className="text-gray-300 block mb-4">{report.summary}</Text>
          <Row gutter={[16, 16]}>
            <Col span={6}>
              <Statistic title="Total Forecasts" value={metrics.total_forecasts} />
            </Col>
            <Col span={6}>
              <Statistic title="Win Rate" value={(metrics.win_rate * 100).toFixed(2)} suffix="%" valueStyle={{ color: metrics.win_rate >= 0.5 ? '#3f8600' : '#cf1322' }} />
            </Col>
            <Col span={6}>
              <Statistic title="Sharpe Ratio" value={metrics.sharpe_ratio} />
            </Col>
            <Col span={6}>
              <Statistic title="Profit Factor" value={metrics.profit_factor} />
            </Col>
            
            <Col span={6}>
              <Statistic title="Calmar Ratio" value={metrics.calmar_ratio} />
            </Col>
            <Col span={6}>
              <Statistic title="Sortino Ratio" value={metrics.sortino_ratio} />
            </Col>
            <Col span={6}>
              <Statistic title="Precision" value={(metrics.precision * 100).toFixed(2)} suffix="%" />
            </Col>
            <Col span={6}>
              <Statistic title="Recall" value={(metrics.recall * 100).toFixed(2)} suffix="%" />
            </Col>

            <Col span={6}>
              <Statistic title="Avg Return" value={(metrics.average_return * 100).toFixed(4)} suffix="%" />
            </Col>
            <Col span={6}>
              <Statistic title="Max Drawdown" value={metrics.max_drawdown} valueStyle={{ color: '#cf1322' }} />
            </Col>
            <Col span={6}>
              <Statistic title="RMSE" value={metrics.rmse} />
            </Col>
            <Col span={6}>
              <Statistic title="Avg Holding Error" value={metrics.avg_holding_error} suffix="m" />
            </Col>
          </Row>
        </Card>

        {rankings && (
          <Row gutter={16}>
            <Col span={8}>
              <Card title="Top Assets" className="bg-gray-800 border-gray-700">
                <Table 
                  dataSource={rankings.top_assets} 
                  pagination={false} 
                  size="small"
                  rowKey="asset"
                  columns={[
                    { title: 'Asset', dataIndex: 'asset', key: 'asset' },
                    { title: 'Win Rate', dataIndex: 'win_rate', key: 'win_rate', render: val => `${(val * 100).toFixed(1)}%` }
                  ]} 
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card title="Top Timeframes" className="bg-gray-800 border-gray-700">
                <Table 
                  dataSource={rankings.top_timeframes} 
                  pagination={false} 
                  size="small"
                  rowKey="timeframe"
                  columns={[
                    { title: 'Timeframe', dataIndex: 'timeframe', key: 'timeframe' },
                    { title: 'Win Rate', dataIndex: 'win_rate', key: 'win_rate', render: val => `${(val * 100).toFixed(1)}%` }
                  ]} 
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card title="Top Strategies" className="bg-gray-800 border-gray-700">
                <Table 
                  dataSource={rankings.top_strategies} 
                  pagination={false} 
                  size="small"
                  rowKey="strategy"
                  columns={[
                    { title: 'Strategy', dataIndex: 'strategy', key: 'strategy' },
                    { title: 'Profit Factor', dataIndex: 'profit_factor', key: 'profit_factor' }
                  ]} 
                />
              </Card>
            </Col>
          </Row>
        )}
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 h-full overflow-y-auto">
      <div className="flex items-center space-x-3 border-b border-gray-700 pb-4">
        <FileText className="text-3xl text-blue-400" />
        <Title level={2} className="!mb-0 text-gray-100">AI Research Validation Dashboard</Title>
      </div>
      
      <Row gutter={16}>
        <Col span={6}>
          <Card className="bg-gray-800 border-gray-700">
            <Statistic title="Today's Accuracy" value={reports?.daily?.metrics?.overall_accuracy ? (reports.daily.metrics.overall_accuracy * 100).toFixed(1) : 0} suffix="%" prefix={<Activity className="w-4 h-4 mr-2" />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="bg-gray-800 border-gray-700">
            <Statistic title="Best Model" value={reports?.monthly?.rankings?.top_strategies?.[0]?.strategy || "N/A"} prefix={<BrainCircuit className="w-4 h-4 mr-2" />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="bg-gray-800 border-gray-700">
            <Statistic title="Total Validated" value={reports?.monthly?.metrics?.total_forecasts || 0} prefix={<Database className="w-4 h-4 mr-2" />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="bg-gray-800 border-gray-700">
            <Statistic title="Validation Engine" value="Active" valueStyle={{ color: '#3f8600' }} prefix={<TrendingUp className="w-4 h-4 mr-2" />} />
          </Card>
        </Col>
      </Row>
      
      <Card title={<span><BarChart2 className="inline mr-2" /> Validation Reports</span>} className="bg-gray-800 border-gray-700">
        {loading ? (
          <Spin size="large" className="flex justify-center" />
        ) : (
          <Tabs defaultActiveKey="daily">
            <TabPane tab="Daily Report" key="daily">
              {renderReportCard('daily')}
            </TabPane>
            <TabPane tab="Weekly Report" key="weekly">
              {renderReportCard('weekly')}
            </TabPane>
            <TabPane tab="Monthly Report" key="monthly">
              {renderReportCard('monthly')}
            </TabPane>
            <TabPane tab="Quarterly Report" key="quarterly">
              {renderReportCard('quarterly')}
            </TabPane>
          </Tabs>
        )}
      </Card>
    </div>
  );
};
