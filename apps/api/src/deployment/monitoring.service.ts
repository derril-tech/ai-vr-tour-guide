import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

interface MetricData {
  name: string;
  value: number;
  timestamp: number;
  labels: Record<string, string>;
  unit?: string;
}

interface AlertRule {
  id: string;
  name: string;
  metric: string;
  condition: 'gt' | 'lt' | 'eq' | 'ne';
  threshold: number;
  duration: number; // seconds
  severity: 'low' | 'medium' | 'high' | 'critical';
  enabled: boolean;
}

@Injectable()
export class MonitoringService {
  private readonly logger = new Logger(MonitoringService.name);
  private metrics: Map<string, MetricData[]> = new Map();
  private alertRules: AlertRule[] = [];

  constructor(private configService: ConfigService) {
    this.initializeDefaultAlertRules();
    this.startMetricsCollection();
  }

  /**
   * Initialize default monitoring alert rules
   */
  private initializeDefaultAlertRules(): void {
    this.alertRules = [
      // API Performance
      {
        id: 'api_response_time',
        name: 'High API Response Time',
        metric: 'http_request_duration_ms',
        condition: 'gt',
        threshold: 5000,
        duration: 300,
        severity: 'high',
        enabled: true,
      },
      {
        id: 'api_error_rate',
        name: 'High API Error Rate',
        metric: 'http_requests_error_rate',
        condition: 'gt',
        threshold: 0.05, // 5%
        duration: 180,
        severity: 'critical',
        enabled: true,
      },

      // System Resources
      {
        id: 'cpu_usage',
        name: 'High CPU Usage',
        metric: 'system_cpu_usage_percent',
        condition: 'gt',
        threshold: 80,
        duration: 600,
        severity: 'medium',
        enabled: true,
      },
      {
        id: 'memory_usage',
        name: 'High Memory Usage',
        metric: 'system_memory_usage_percent',
        condition: 'gt',
        threshold: 85,
        duration: 300,
        severity: 'high',
        enabled: true,
      },
      {
        id: 'disk_usage',
        name: 'High Disk Usage',
        metric: 'system_disk_usage_percent',
        condition: 'gt',
        threshold: 90,
        duration: 900,
        severity: 'critical',
        enabled: true,
      },

      // Database
      {
        id: 'db_connection_pool',
        name: 'Database Connection Pool Exhaustion',
        metric: 'db_connection_pool_usage_percent',
        condition: 'gt',
        threshold: 90,
        duration: 120,
        severity: 'critical',
        enabled: true,
      },
      {
        id: 'db_query_time',
        name: 'Slow Database Queries',
        metric: 'db_query_duration_ms',
        condition: 'gt',
        threshold: 10000,
        duration: 300,
        severity: 'medium',
        enabled: true,
      },

      // AI Services
      {
        id: 'llm_response_time',
        name: 'Slow LLM Response',
        metric: 'llm_request_duration_ms',
        condition: 'gt',
        threshold: 30000,
        duration: 180,
        severity: 'medium',
        enabled: true,
      },
      {
        id: 'embedding_queue_size',
        name: 'Large Embedding Queue',
        metric: 'embedding_queue_size',
        condition: 'gt',
        threshold: 1000,
        duration: 600,
        severity: 'medium',
        enabled: true,
      },

      // VR Performance
      {
        id: 'vr_frame_rate',
        name: 'Low VR Frame Rate',
        metric: 'vr_fps',
        condition: 'lt',
        threshold: 72,
        duration: 60,
        severity: 'high',
        enabled: true,
      },
      {
        id: 'vr_comfort_score',
        name: 'Poor VR Comfort Score',
        metric: 'vr_comfort_score',
        condition: 'lt',
        threshold: 0.7,
        duration: 120,
        severity: 'medium',
        enabled: true,
      },

      // Business Metrics
      {
        id: 'active_users',
        name: 'Low Active Users',
        metric: 'active_users_count',
        condition: 'lt',
        threshold: 10,
        duration: 1800,
        severity: 'low',
        enabled: true,
      },
      {
        id: 'tour_completion_rate',
        name: 'Low Tour Completion Rate',
        metric: 'tour_completion_rate',
        condition: 'lt',
        threshold: 0.6,
        duration: 3600,
        severity: 'medium',
        enabled: true,
      },
    ];

    this.logger.log(`Initialized ${this.alertRules.length} monitoring alert rules`);
  }

  /**
   * Start collecting system metrics
   */
  private startMetricsCollection(): void {
    // Collect metrics every 30 seconds
    setInterval(() => {
      this.collectSystemMetrics();
    }, 30000);

    // Collect application metrics every 60 seconds
    setInterval(() => {
      this.collectApplicationMetrics();
    }, 60000);

    this.logger.log('Started metrics collection');
  }

  /**
   * Record a custom metric
   */
  recordMetric(name: string, value: number, labels: Record<string, string> = {}, unit?: string): void {
    const metric: MetricData = {
      name,
      value,
      timestamp: Date.now(),
      labels,
      unit,
    };

    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }

    const metricHistory = this.metrics.get(name)!;
    metricHistory.push(metric);

    // Keep only last 1000 data points per metric
    if (metricHistory.length > 1000) {
      metricHistory.shift();
    }

    // Check alert rules
    this.checkAlertRules(name, value, labels);
  }

  /**
   * Get metric data
   */
  getMetric(name: string, timeRange?: { start: number; end: number }): MetricData[] {
    const metricHistory = this.metrics.get(name) || [];

    if (!timeRange) {
      return metricHistory;
    }

    return metricHistory.filter(
      metric => metric.timestamp >= timeRange.start && metric.timestamp <= timeRange.end
    );
  }

  /**
   * Get all available metrics
   */
  getAllMetrics(): string[] {
    return Array.from(this.metrics.keys());
  }

  /**
   * Get system health dashboard data
   */
  getHealthDashboard(): any {
    const now = Date.now();
    const oneHourAgo = now - 3600000; // 1 hour

    return {
      timestamp: now,
      system: {
        cpu: this.getLatestMetricValue('system_cpu_usage_percent'),
        memory: this.getLatestMetricValue('system_memory_usage_percent'),
        disk: this.getLatestMetricValue('system_disk_usage_percent'),
      },
      api: {
        responseTime: this.getAverageMetricValue('http_request_duration_ms', oneHourAgo),
        errorRate: this.getAverageMetricValue('http_requests_error_rate', oneHourAgo),
        requestsPerMinute: this.getMetricRate('http_requests_total', oneHourAgo),
      },
      database: {
        connectionPoolUsage: this.getLatestMetricValue('db_connection_pool_usage_percent'),
        queryTime: this.getAverageMetricValue('db_query_duration_ms', oneHourAgo),
        activeConnections: this.getLatestMetricValue('db_active_connections'),
      },
      ai: {
        llmResponseTime: this.getAverageMetricValue('llm_request_duration_ms', oneHourAgo),
        embeddingQueueSize: this.getLatestMetricValue('embedding_queue_size'),
        ragAccuracy: this.getLatestMetricValue('rag_accuracy_score'),
      },
      vr: {
        averageFps: this.getAverageMetricValue('vr_fps', oneHourAgo),
        comfortScore: this.getAverageMetricValue('vr_comfort_score', oneHourAgo),
        activeVrSessions: this.getLatestMetricValue('vr_active_sessions'),
      },
      business: {
        activeUsers: this.getLatestMetricValue('active_users_count'),
        tourCompletionRate: this.getAverageMetricValue('tour_completion_rate', oneHourAgo),
        revenue: this.getLatestMetricValue('revenue_total'),
      },
    };
  }

  /**
   * Collect system metrics
   */
  private collectSystemMetrics(): void {
    // In a real implementation, this would collect actual system metrics
    // For now, we'll simulate some metrics

    // CPU Usage
    const cpuUsage = Math.random() * 100;
    this.recordMetric('system_cpu_usage_percent', cpuUsage, { host: 'api-server' }, '%');

    // Memory Usage
    const memoryUsage = 60 + Math.random() * 30;
    this.recordMetric('system_memory_usage_percent', memoryUsage, { host: 'api-server' }, '%');

    // Disk Usage
    const diskUsage = 45 + Math.random() * 20;
    this.recordMetric('system_disk_usage_percent', diskUsage, { host: 'api-server' }, '%');
  }

  /**
   * Collect application metrics
   */
  private collectApplicationMetrics(): void {
    // Simulate application metrics

    // API Response Time
    const responseTime = 500 + Math.random() * 2000;
    this.recordMetric('http_request_duration_ms', responseTime, { endpoint: '/api/tours' }, 'ms');

    // Error Rate
    const errorRate = Math.random() * 0.1; // 0-10%
    this.recordMetric('http_requests_error_rate', errorRate, { service: 'api' }, 'rate');

    // Database Connection Pool
    const dbPoolUsage = 30 + Math.random() * 40;
    this.recordMetric('db_connection_pool_usage_percent', dbPoolUsage, { database: 'postgres' }, '%');

    // Active Users
    const activeUsers = 50 + Math.floor(Math.random() * 200);
    this.recordMetric('active_users_count', activeUsers, { service: 'api' }, 'count');

    // VR Metrics
    const vrFps = 72 + Math.random() * 18; // 72-90 FPS
    this.recordMetric('vr_fps', vrFps, { platform: 'quest' }, 'fps');

    const comfortScore = 0.7 + Math.random() * 0.3;
    this.recordMetric('vr_comfort_score', comfortScore, { platform: 'quest' }, 'score');
  }

  /**
   * Check alert rules against metric values
   */
  private checkAlertRules(metricName: string, value: number, labels: Record<string, string>): void {
    const relevantRules = this.alertRules.filter(rule => 
      rule.enabled && rule.metric === metricName
    );

    for (const rule of relevantRules) {
      const shouldAlert = this.evaluateAlertCondition(rule, value);
      
      if (shouldAlert) {
        this.triggerAlert(rule, value, labels);
      }
    }
  }

  /**
   * Evaluate alert condition
   */
  private evaluateAlertCondition(rule: AlertRule, value: number): boolean {
    switch (rule.condition) {
      case 'gt':
        return value > rule.threshold;
      case 'lt':
        return value < rule.threshold;
      case 'eq':
        return value === rule.threshold;
      case 'ne':
        return value !== rule.threshold;
      default:
        return false;
    }
  }

  /**
   * Trigger an alert
   */
  private triggerAlert(rule: AlertRule, value: number, labels: Record<string, string>): void {
    const alert = {
      id: `${rule.id}_${Date.now()}`,
      ruleName: rule.name,
      metric: rule.metric,
      value,
      threshold: rule.threshold,
      severity: rule.severity,
      labels,
      timestamp: new Date().toISOString(),
    };

    this.logger.warn(`ALERT: ${rule.name} - ${rule.metric} = ${value} (threshold: ${rule.threshold})`);

    // In a real implementation, this would send alerts via email, Slack, PagerDuty, etc.
    this.sendAlert(alert);
  }

  /**
   * Send alert notification
   */
  private sendAlert(alert: any): void {
    // This would integrate with alerting systems
    // For now, just log the alert
    this.logger.warn(`Alert sent: ${JSON.stringify(alert)}`);
  }

  /**
   * Helper methods for metric calculations
   */
  private getLatestMetricValue(metricName: string): number | null {
    const metricHistory = this.metrics.get(metricName);
    if (!metricHistory || metricHistory.length === 0) {
      return null;
    }
    return metricHistory[metricHistory.length - 1].value;
  }

  private getAverageMetricValue(metricName: string, since: number): number | null {
    const metricHistory = this.metrics.get(metricName);
    if (!metricHistory || metricHistory.length === 0) {
      return null;
    }

    const recentMetrics = metricHistory.filter(m => m.timestamp >= since);
    if (recentMetrics.length === 0) {
      return null;
    }

    const sum = recentMetrics.reduce((acc, m) => acc + m.value, 0);
    return sum / recentMetrics.length;
  }

  private getMetricRate(metricName: string, since: number): number | null {
    const metricHistory = this.metrics.get(metricName);
    if (!metricHistory || metricHistory.length === 0) {
      return null;
    }

    const recentMetrics = metricHistory.filter(m => m.timestamp >= since);
    const timeSpanMinutes = (Date.now() - since) / 60000;
    
    return recentMetrics.length / timeSpanMinutes;
  }

  /**
   * Get alert rules
   */
  getAlertRules(): AlertRule[] {
    return this.alertRules;
  }

  /**
   * Update alert rule
   */
  updateAlertRule(ruleId: string, updates: Partial<AlertRule>): void {
    const ruleIndex = this.alertRules.findIndex(rule => rule.id === ruleId);
    if (ruleIndex !== -1) {
      this.alertRules[ruleIndex] = { ...this.alertRules[ruleIndex], ...updates };
      this.logger.log(`Updated alert rule: ${ruleId}`);
    }
  }

  /**
   * Export metrics for external monitoring systems
   */
  exportMetrics(format: 'prometheus' | 'json' = 'json'): string {
    if (format === 'prometheus') {
      return this.exportPrometheusFormat();
    }
    
    const allMetrics = {};
    for (const [name, history] of this.metrics.entries()) {
      allMetrics[name] = history[history.length - 1]; // Latest value
    }
    
    return JSON.stringify(allMetrics, null, 2);
  }

  private exportPrometheusFormat(): string {
    let output = '';
    
    for (const [name, history] of this.metrics.entries()) {
      const latest = history[history.length - 1];
      if (latest) {
        const labels = Object.entries(latest.labels)
          .map(([key, value]) => `${key}="${value}"`)
          .join(',');
        
        output += `# HELP ${name} ${name}\n`;
        output += `# TYPE ${name} gauge\n`;
        output += `${name}{${labels}} ${latest.value}\n\n`;
      }
    }
    
    return output;
  }
}
