#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时基金估值获取工具
从天天基金和新浪财经获取基金实时估值数据
"""

import requests
import re
import json
import time
from typing import Optional, Dict, Any, List


class FundValuationFetcher:
    """基金估值获取器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def fetch_fundgz(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """
        从天天基金获取估值数据 (数据源1)
        
        Args:
            fund_code: 基金代码，6位数字
            
        Returns:
            估值数据字典，失败返回None
        """
        url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js?rt={int(time.time() * 1000)}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 解析JSONP格式
            text = response.text.strip()
            # 匹配 jsonpgz({...}) 格式
            match = re.search(r'jsonpgz\((.*)\);', text)
            if not match:
                return None
            
            data = json.loads(match.group(1))
            
            return {
                'code': data.get('fundcode'),
                'name': data.get('name'),
                'gsz': float(data.get('gsz', 0)) if data.get('gsz') else None,  # 估算净值
                'gszzl': float(data.get('gszzl', 0)) if data.get('gszzl') else None,  # 估算涨跌幅
                'gztime': data.get('gztime'),  # 估值时间
                'dwjz': float(data.get('dwjz', 0)) if data.get('dwjz') else None,  # 昨日净值
                'jzrq': data.get('jzrq'),  # 净值日期
                'valuation_source': 'fundgz'
            }
        except Exception as e:
            print(f"获取天天基金估值失败: {e}")
            return None

    def fetch_sina_estimate(self, fund_code: str, data_source: int = 2) -> Optional[Dict[str, Any]]:
        """
        从新浪财经获取估值数据 (数据源2或3)
        
        Args:
            fund_code: 基金代码，6位数字
            data_source: 2 或 3，两种不同口径
            
        Returns:
            估值数据字典，包含分时序列，失败返回None
        """
        url = f"https://stock.finance.sina.com.cn/fundInfo/api/openapi.php/FdFundService.getEstimateNetworthPic?symbol={fund_code}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 解析JSON格式（新浪返回纯JSON，不是JSONP）
            text = response.text.strip()
            result = json.loads(text)
            data = result.get('result', {}).get('data', {})
            networth = data.get('networth', [])
            
            if not networth or not isinstance(networth, list):
                return None
            
            last_point = networth[-1]
            
            # 根据数据源选择不同字段
            if data_source == 2:
                g_rate = last_point.get('growthrate', 0)
                pre_nav = last_point.get('pre_nav')
                nav_key = 'pre_nav'
                gr_key = 'growthrate'
            else:  # data_source == 3
                g_rate = last_point.get('growthrate2')
                pre_nav = last_point.get('pre_nav2')
                nav_key = 'pre_nav2'
                gr_key = 'growthrate2'
            
            # 转换为数字类型
            try:
                g_rate = float(g_rate) if g_rate is not None else None
            except (ValueError, TypeError):
                g_rate = None
                
            try:
                pre_nav = float(pre_nav) if pre_nav is not None else None
            except (ValueError, TypeError):
                pre_nav = None
            
            # 构建分时序列
            timeseries = []
            seen = set()
            for point in networth:
                # 获取估值
                value = point.get(nav_key)
                if value is None:
                    continue
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    continue
                    
                # 获取时间
                time_str = point.get('min_time')
                date_str = point.get('pre_date')
                if not time_str or not date_str:
                    continue
                    
                # 获取涨跌幅
                gr = point.get(gr_key)
                try:
                    gr = float(gr) if gr is not None else None
                except (ValueError, TypeError):
                    gr = None
                    
                key = f"{date_str} {time_str}"
                if key in seen:
                    continue
                seen.add(key)
                timeseries.append({
                    'time': time_str,
                    'value': value,
                    'date': date_str,
                    'growthrate': gr
                })
            
            return {
                'code': fund_code,
                'gsz': pre_nav if pre_nav else None,
                'gztime': f"{last_point.get('pre_date', '')} {last_point.get('min_time', '')}".strip(),
                'gszzl': g_rate * 100 if g_rate is not None else None,
                'valuation_source': f'sina_ds{data_source}',
                'timeseries': timeseries
            }
        except Exception as e:
            print(f"获取新浪财经估值失败: {e}")
            return None

    def fetch_valuation(self, fund_code: str, data_source: int = 1) -> Optional[Dict[str, Any]]:
        """
        获取基金估值，支持多种数据源
        
        Args:
            fund_code: 基金代码
            data_source: 1-天天基金，2-新浪口径1，3-新浪口径2
            
        Returns:
            估值数据字典
        """
        if data_source in (2, 3):
            return self.fetch_sina_estimate(fund_code, data_source)
        else:
            return self.fetch_fundgz(fund_code)
    
    def search_funds(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索基金，根据关键词查找基金
        
        Args:
            keyword: 搜索关键词，可以是基金代码或名称
            
        Returns:
            基金列表，每个元素包含 code 和 name
        """
        # 使用天天基金的搜索接口
        url = f"https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx?m=1&key={keyword}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get('Datas', []):
                results.append({
                    'code': item.get('CODE'),
                    'name': item.get('NAME')
                })
            
            return results
        except Exception as e:
            print(f"搜索基金失败: {e}")
            return []


def test_fund_valuation():
    """测试基金估值获取"""
    fetcher = FundValuationFetcher()
    
    # 测试基金代码
    test_codes = [
        '110022',  # 易方达消费精选
        '001632',  # 天弘中证食品饮料
        '161725',  # 招商中证白酒
    ]
    
    print("=" * 60)
    print("基金估值测试")
    print("=" * 60)
    
    for code in test_codes:
        print(f"\n测试基金: {code}")
        print("-" * 60)
        
        # 测试天天基金
        print("\n[1] 天天基金数据源:")
        fundgz_data = fetcher.fetch_fundgz(code)
        if fundgz_data:
            print(f"  基金名称: {fundgz_data['name']}")
            print(f"  估算净值: {fundgz_data['gsz']}")
            print(f"  估算涨跌: {fundgz_data['gszzl']}%")
            print(f"  估值时间: {fundgz_data['gztime']}")
            print(f"  昨日净值: {fundgz_data['dwjz']}")
        else:
            print("  获取失败")
        
        # 测试新浪数据源2
        print("\n[2] 新浪财经数据源2:")
        sina2_data = fetcher.fetch_sina_estimate(code, 2)
        if sina2_data:
            print(f"  估算净值: {sina2_data['gsz']}")
            print(f"  估算涨跌: {sina2_data['gszzl']}%")
            print(f"  估值时间: {sina2_data['gztime']}")
            print(f"  分时点数: {len(sina2_data['timeseries'])}")
        else:
            print("  获取失败")
        
        # 测试新浪数据源3
        print("\n[3] 新浪财经数据源3:")
        sina3_data = fetcher.fetch_sina_estimate(code, 3)
        if sina3_data:
            print(f"  估算净值: {sina3_data['gsz']}")
            print(f"  估算涨跌: {sina3_data['gszzl']}%")
            print(f"  估值时间: {sina3_data['gztime']}")
            print(f"  分时点数: {len(sina3_data['timeseries'])}")
        else:
            print("  获取失败")


if __name__ == "__main__":
    test_fund_valuation()
