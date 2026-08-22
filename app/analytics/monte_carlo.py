import random


class MonteCarloSimulator:
    def __init__(self, iterations: int = 10000):
        self.iterations = iterations

    def simulate(self, trades: list[dict], initial_balance: float = 100000.0) -> dict:
        if not trades:
            return {}

        results = []
        n_trades = len(trades)
        
        # We sample with replacement to create 10k alternate realities of the trade sequence
        for _ in range(self.iterations):
            simulated_trades = random.choices(trades, k=n_trades)
            
            balance = initial_balance
            peak = initial_balance
            max_dd = 0.0
            ruined = False
            
            path = [initial_balance]
            for t in simulated_trades:
                balance += t.get("pnl", 0)
                path.append(balance)
                if balance <= 0:
                    ruined = True
                    break
                
                peak = max(peak, balance)
                    
                dd = (peak - balance) / peak
                max_dd = max(max_dd, dd)
                    
            cagr = (balance / initial_balance) if not ruined else 0
            results.append({
                "ruined": ruined,
                "max_dd": max_dd,
                "cagr": cagr,
                "path": path
            })

        ruin_count = sum(1 for r in results if r["ruined"])
        prob_ruin = (ruin_count / self.iterations) * 100
        
        valid_results = [r for r in results if not r["ruined"]]
        if not valid_results:
            return {"probability_of_ruin": 100.0}
            
        valid_results.sort(key=lambda x: x["cagr"])
        cagrs = [r["cagr"] for r in valid_results]
        dds = sorted([r["max_dd"] for r in valid_results], reverse=True)
        
        # 95% Confidence Interval (drop bottom 2.5% and top 2.5%)
        lower_bound_idx = int(len(cagrs) * 0.025)
        upper_bound_idx = int(len(cagrs) * 0.975)
        
        # Get sample paths
        median_idx = int(len(cagrs) * 0.5)
        p5_idx = int(len(cagrs) * 0.05)
        p95_idx = int(len(cagrs) * 0.95)
        
        sample_paths = {
            "median": valid_results[median_idx]["path"],
            "p5": valid_results[p5_idx]["path"],
            "p95": valid_results[p95_idx]["path"],
        }
        
        if len(valid_results) > 10:
            import random as rnd
            sample_paths["random_1"] = rnd.choice(valid_results)["path"]
            sample_paths["random_2"] = rnd.choice(valid_results)["path"]
        
        return {
            "probability_of_ruin": prob_ruin,
            "worst_expected_drawdown": dds[int(len(dds) * 0.05)] * 100, # 95th percentile worst DD
            "expected_cagr_median": cagrs[median_idx],
            "cagr_95_ci_lower": cagrs[lower_bound_idx],
            "cagr_95_ci_upper": cagrs[upper_bound_idx],
            "sample_paths": sample_paths
        }
