import unittest
import tempfile
import shutil
import sys
from pathlib import Path
from typing import AnyStr, List, Dict, Any

sys.path.insert(0, "experiment-runner")

from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunTableModel import RunTableModel
from ConfigValidator.Config.RunnerConfig import RunnerConfig
from ProgressManager.Output.OutputProcedure import OutputProcedure as output


class RemoteAgent:
    """Mock remote agent for testing distributed execution"""
    def __init__(self, agent_id: str, host: str, port: int):
        self.agent_id = agent_id
        self.host = host
        self.port = port
        self.is_connected = False
        self.assigned_runs: List[Dict] = []
        self.completed_runs: List[Dict] = []
        self.failed_runs: List[str] = []

    def connect(self) -> bool:
        """Simulate connection to remote agent"""
        if not self.host or self.port <= 0:
            return False
        self.is_connected = True
        return True

    def disconnect(self) -> bool:
        """Disconnect from remote agent"""
        self.is_connected = False
        return True

    def send_run(self, run_data: Dict) -> bool:
        """Send a run to the remote agent for execution"""
        if not self.is_connected:
            return False
        self.assigned_runs.append(run_data)
        return True

    def retrieve_results(self) -> List[Dict]:
        """Retrieve completed run results from remote agent"""
        return self.completed_runs.copy()

    def mark_run_complete(self, run_id: str, result_data: Dict) -> bool:
        """Mark a run as completed on the remote agent"""
        result_data['__run_id'] = run_id
        self.completed_runs.append(result_data)
        self.assigned_runs = [r for r in self.assigned_runs if r.get('__run_id') != run_id]
        return True

    def mark_run_failed(self, run_id: str, error_message: str) -> bool:
        """Mark a run as failed"""
        self.failed_runs.append(run_id)
        self.assigned_runs = [r for r in self.assigned_runs if r.get('__run_id') != run_id]
        return True


class RemoteDistributionManager:
    """Manages distribution of experiments across remote agents"""
    def __init__(self):
        self.agents: Dict[str, RemoteAgent] = {}
        self.pending_runs: List[Dict] = []
        self.completed_runs: List[Dict] = []
        self.failed_runs: Dict[str, str] = {}

    def register_agent(self, agent: RemoteAgent) -> bool:
        """Register a new remote agent"""
        if not isinstance(agent, RemoteAgent):
            return False
        self.agents[agent.agent_id] = agent
        return True

    def connect_all_agents(self) -> Dict[str, bool]:
        """Connect to all registered agents"""
        results = {}
        for agent_id, agent in self.agents.items():
            results[agent_id] = agent.connect()
        return results

    def disconnect_all_agents(self) -> Dict[str, bool]:
        """Disconnect from all agents"""
        results = {}
        for agent_id, agent in self.agents.items():
            results[agent_id] = agent.disconnect()
        return results

    def distribute_runs(self, runs: List[Dict]) -> Dict[str, int]:
        """Distribute runs across available agents using round-robin"""
        self.pending_runs = runs.copy()
        agent_ids = list(self.agents.keys())
        
        if not agent_ids:
            self.failed_runs.update({r.get('__run_id'): 'No agents available' for r in runs})
            return {'distributed': 0, 'failed': len(runs)}

        distributed = 0
        failed = 0
        
        for idx, run in enumerate(runs):
            agent_id = agent_ids[idx % len(agent_ids)]
            agent = self.agents[agent_id]
            
            if agent.send_run(run):
                distributed += 1
            else:
                self.failed_runs[run.get('__run_id')] = f'Failed to send to agent {agent_id}'
                failed += 1

        return {'distributed': distributed, 'failed': failed}

    def collect_results(self) -> Dict[str, Any]:
        """Collect results from all agents"""
        for agent in self.agents.values():
            self.completed_runs.extend(agent.retrieve_results())
        
        return {
            'total_completed': len(self.completed_runs),
            'total_failed': len(self.failed_runs),
            'results': self.completed_runs
        }

    def get_agent_status(self) -> Dict[str, Dict]:
        """Get status of all agents"""
        status = {}
        for agent_id, agent in self.agents.items():
            status[agent_id] = {
                'connected': agent.is_connected,
                'assigned_runs': len(agent.assigned_runs),
                'completed_runs': len(agent.completed_runs),
                'failed_runs': len(agent.failed_runs),
                'host': agent.host,
                'port': agent.port
            }
        return status


class TestRemoteAgentBasic(unittest.TestCase):
    """Test basic remote agent functionality"""

    def setUp(self):
        self.agent = RemoteAgent(
            agent_id="test_agent_1",
            host="localhost",
            port=8000
        )

    def test_agent_initialization(self):
        """Test that agent is properly initialized"""
        self.assertEqual(self.agent.agent_id, "test_agent_1")
        self.assertEqual(self.agent.host, "localhost")
        self.assertEqual(self.agent.port, 8000)
        self.assertFalse(self.agent.is_connected)

    def test_agent_connection(self):
        """Test connecting to remote agent"""
        self.assertFalse(self.agent.is_connected)
        connected = self.agent.connect()
        self.assertTrue(connected)
        self.assertTrue(self.agent.is_connected)

    def test_agent_disconnection(self):
        """Test disconnecting from remote agent"""
        self.agent.connect()
        self.assertTrue(self.agent.is_connected)
        disconnected = self.agent.disconnect()
        self.assertTrue(disconnected)
        self.assertFalse(self.agent.is_connected)

    def test_invalid_agent_connection(self):
        """Test connection failure with invalid parameters"""
        invalid_agent = RemoteAgent("invalid", "", -1)
        connected = invalid_agent.connect()
        self.assertFalse(connected)
        self.assertFalse(invalid_agent.is_connected)


class TestRemoteAgentRunManagement(unittest.TestCase):
    """Test run management on remote agents"""

    def setUp(self):
        self.agent = RemoteAgent("test_agent", "localhost", 8000)
        self.agent.connect()
        self.test_run = {
            '__run_id': 'run_1',
            'factor1': 'treatment1',
            'factor2': 'value1'
        }

    def tearDown(self):
        self.agent.disconnect()

    def test_send_run_when_connected(self):
        """Test sending a run to connected agent"""
        result = self.agent.send_run(self.test_run)
        self.assertTrue(result)
        self.assertEqual(len(self.agent.assigned_runs), 1)
        self.assertEqual(self.agent.assigned_runs[0]['__run_id'], 'run_1')

    def test_send_run_when_disconnected(self):
        """Test that runs cannot be sent to disconnected agent"""
        self.agent.disconnect()
        result = self.agent.send_run(self.test_run)
        self.assertFalse(result)
        self.assertEqual(len(self.agent.assigned_runs), 0)

    def test_mark_run_complete(self):
        """Test marking a run as completed"""
        self.agent.send_run(self.test_run)
        result_data = {'result_col': 42.5}
        
        success = self.agent.mark_run_complete('run_1', result_data)
        self.assertTrue(success)
        self.assertEqual(len(self.agent.completed_runs), 1)
        self.assertEqual(self.agent.completed_runs[0]['result_col'], 42.5)
        self.assertEqual(self.agent.completed_runs[0]['__run_id'], 'run_1')
        self.assertEqual(len(self.agent.assigned_runs), 0)

    def test_mark_run_failed(self):
        """Test marking a run as failed"""
        self.agent.send_run(self.test_run)
        
        success = self.agent.mark_run_failed('run_1', 'Timeout error')
        self.assertTrue(success)
        self.assertEqual(len(self.agent.failed_runs), 1)
        self.assertIn('run_1', self.agent.failed_runs)
        self.assertEqual(len(self.agent.assigned_runs), 0)

    def test_retrieve_results(self):
        """Test retrieving results from agent"""
        self.agent.send_run(self.test_run)
        self.agent.mark_run_complete('run_1', {'data': 100})
        
        results = self.agent.retrieve_results()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['data'], 100)


class TestRemoteDistributionManagerBasic(unittest.TestCase):
    """Test basic distribution manager functionality"""

    def setUp(self):
        self.manager = RemoteDistributionManager()
        self.agent1 = RemoteAgent("agent_1", "host1.local", 8000)
        self.agent2 = RemoteAgent("agent_2", "host2.local", 8001)

    def test_manager_initialization(self):
        """Test distribution manager initialization"""
        self.assertEqual(len(self.manager.agents), 0)
        self.assertEqual(len(self.manager.pending_runs), 0)

    def test_register_agents(self):
        """Test registering remote agents"""
        success1 = self.manager.register_agent(self.agent1)
        success2 = self.manager.register_agent(self.agent2)
        
        self.assertTrue(success1)
        self.assertTrue(success2)
        self.assertEqual(len(self.manager.agents), 2)

    def test_register_invalid_agent(self):
        """Test that invalid objects cannot be registered"""
        result = self.manager.register_agent("not_an_agent")
        self.assertFalse(result)

    def test_connect_all_agents(self):
        """Test connecting all registered agents"""
        self.manager.register_agent(self.agent1)
        self.manager.register_agent(self.agent2)
        
        results = self.manager.connect_all_agents()
        
        self.assertEqual(results['agent_1'], True)
        self.assertEqual(results['agent_2'], True)
        self.assertTrue(self.agent1.is_connected)
        self.assertTrue(self.agent2.is_connected)

    def test_disconnect_all_agents(self):
        """Test disconnecting all agents"""
        self.manager.register_agent(self.agent1)
        self.manager.register_agent(self.agent2)
        self.manager.connect_all_agents()
        
        results = self.manager.disconnect_all_agents()
        
        self.assertEqual(results['agent_1'], True)
        self.assertEqual(results['agent_2'], True)
        self.assertFalse(self.agent1.is_connected)
        self.assertFalse(self.agent2.is_connected)


class TestDistributionAlgorithms(unittest.TestCase):
    """Test distribution algorithms"""

    def setUp(self):
        self.manager = RemoteDistributionManager()
        self.agent1 = RemoteAgent("agent_1", "host1.local", 8000)
        self.agent2 = RemoteAgent("agent_2", "host2.local", 8001)
        
        self.manager.register_agent(self.agent1)
        self.manager.register_agent(self.agent2)
        self.manager.connect_all_agents()

    def test_round_robin_distribution(self):
        """Test round-robin distribution across agents"""
        runs = [
            {'__run_id': f'run_{i}', 'factor': i} 
            for i in range(6)
        ]
        
        distribution = self.manager.distribute_runs(runs)
        
        self.assertEqual(distribution['distributed'], 6)
        self.assertEqual(distribution['failed'], 0)
        self.assertEqual(len(self.agent1.assigned_runs), 3)
        self.assertEqual(len(self.agent2.assigned_runs), 3)

    def test_distribution_to_single_agent(self):
        """Test distribution when only one agent is available"""
        single_manager = RemoteDistributionManager()
        single_manager.register_agent(self.agent1)
        single_manager.connect_all_agents()
        
        runs = [
            {'__run_id': f'run_{i}', 'factor': i} 
            for i in range(4)
        ]
        
        distribution = single_manager.distribute_runs(runs)
        
        self.assertEqual(distribution['distributed'], 4)
        self.assertEqual(len(self.agent1.assigned_runs), 4)

    def test_distribution_with_no_agents(self):
        """Test distribution fails gracefully with no agents"""
        empty_manager = RemoteDistributionManager()
        
        runs = [{'__run_id': 'run_1', 'factor': 1}]
        distribution = empty_manager.distribute_runs(runs)
        
        self.assertEqual(distribution['distributed'], 0)
        self.assertEqual(distribution['failed'], 1)


class TestResultAggregation(unittest.TestCase):
    """Test result aggregation from multiple agents"""

    def setUp(self):
        self.manager = RemoteDistributionManager()
        self.agent1 = RemoteAgent("agent_1", "host1.local", 8000)
        self.agent2 = RemoteAgent("agent_2", "host2.local", 8001)
        
        self.manager.register_agent(self.agent1)
        self.manager.register_agent(self.agent2)
        self.manager.connect_all_agents()

    def test_collect_results_from_multiple_agents(self):
        """Test collecting results from all agents"""
        runs = [
            {'__run_id': f'run_{i}', 'factor': i} 
            for i in range(4)
        ]
        
        self.manager.distribute_runs(runs)
        
        self.agent1.mark_run_complete('run_0', {'result': 100})
        self.agent1.mark_run_complete('run_2', {'result': 150})
        self.agent2.mark_run_complete('run_1', {'result': 120})
        self.agent2.mark_run_complete('run_3', {'result': 180})
        
        aggregation = self.manager.collect_results()
        
        self.assertEqual(aggregation['total_completed'], 4)
        self.assertEqual(aggregation['total_failed'], 0)
        self.assertEqual(len(aggregation['results']), 4)

    def test_agent_status_reporting(self):
        """Test getting status of all agents"""
        runs = [
            {'__run_id': f'run_{i}', 'factor': i} 
            for i in range(4)
        ]
        
        self.manager.distribute_runs(runs)
        self.agent1.mark_run_complete('run_0', {'result': 100})
        
        status = self.manager.get_agent_status()
        
        self.assertEqual(status['agent_1']['assigned_runs'], 1)
        self.assertEqual(status['agent_1']['completed_runs'], 1)
        self.assertEqual(status['agent_2']['assigned_runs'], 2)
        self.assertEqual(status['agent_2']['completed_runs'], 0)


class RemoteDistributionTestConfig(RunnerConfig):
    """Test configuration for remote distribution experiments"""
    
    tmpdir: AnyStr = tempfile.mkdtemp()

    def clear(self):
        if Path(self.__class__.tmpdir).exists():
            shutil.rmtree(self.__class__.tmpdir)

    def create_run_table_model(self):
        return RunTableModel(
            factors=[
                FactorModel("algorithm", ["quicksort", "mergesort", "heapsort"]),
                FactorModel("data_size", [100, 1000, 10000]),
            ],
            data_columns=['execution_time', 'memory_used']
        )

    def start_measurement(self, context: RunnerContext):
        output.console_log("RemoteDistribution: Starting measurement")
        pass

    def interact(self, context: RunnerContext):
        output.console_log("RemoteDistribution: Executing on remote agent")
        pass

    def stop_measurement(self, context: RunnerContext):
        output.console_log("RemoteDistribution: Stopping measurement")
        pass

    def populate_run_data(self, context: RunnerContext):
        output.console_log("RemoteDistribution: Populating run data")
        return {
            'execution_time': 1.5,
            'memory_used': 512
        }


class TestRemoteDistributionIntegration(unittest.TestCase):
    """Integration tests for remote distribution with RunnerConfig"""

    def setUp(self):
        self.config = RemoteDistributionTestConfig()
        self.run_table = self.config.create_run_table_model().generate_experiment_run_table()

    def tearDown(self):
        self.config.clear()

    def test_config_with_remote_distribution(self):
        """Test that config works with remote distribution"""
        self.config.start_measurement(None)
        self.config.interact(None)
        self.config.stop_measurement(None)
        run_data = self.config.populate_run_data(None)
        
        self.assertIsNotNone(run_data)
        self.assertEqual(run_data['execution_time'], 1.5)
        self.assertEqual(run_data['memory_used'], 512)

    def test_run_table_generation_for_distribution(self):
        """Test that run table can be properly distributed"""
        self.assertGreater(len(self.run_table), 0)
        
        for run in self.run_table:
            self.assertIn('__run_id', run)
            self.assertIn('algorithm', run)
            self.assertIn('data_size', run)
            self.assertIn('execution_time', run)
            self.assertIn('memory_used', run)

    def test_distributed_execution_simulation(self):
        """Test simulating distributed execution of experiment"""
        manager = RemoteDistributionManager()
        agent1 = RemoteAgent("agent_1", "localhost", 8000)
        agent2 = RemoteAgent("agent_2", "localhost", 8001)
        
        manager.register_agent(agent1)
        manager.register_agent(agent2)
        manager.connect_all_agents()
        
        distribution = manager.distribute_runs(self.run_table)
        self.assertEqual(distribution['distributed'], len(self.run_table))
        
        for run in self.run_table:
            run_id = run['__run_id']
            manager.agents['agent_1'].mark_run_complete(run_id, self.config.populate_run_data(None))
        
        aggregation = manager.collect_results()
        self.assertGreater(aggregation['total_completed'], 0)


if __name__ == '__main__':
    unittest.main()
