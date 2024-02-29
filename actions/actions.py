# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl
from rasa_sdk.events import AllSlotsReset, Restarted, ConversationPaused
import sys
import os


from datetime import datetime

def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break

    return obj

def wait_for_tasks(si, tasks):
    """Given the service instance and tasks, it returns after all the
   tasks are complete
   """
    property_collector = si.content.propertyCollector
    task_list = [str(task) for task in tasks]
    # Create filter
    obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                 for task in tasks]
    property_spec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                               pathSet=[],
                                                               all=True)
    filter_spec = vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = obj_specs
    filter_spec.propSet = [property_spec]
    pcfilter = property_collector.CreateFilter(filter_spec, True)
    try:
        version, state = None, None
        # Loop looking for updates till the state moves to a completed state.
        while task_list:
            update = property_collector.WaitForUpdates(version)
            for filter_set in update.filterSet:
                for obj_set in filter_set.objectSet:
                    task = obj_set.obj
                    for change in obj_set.changeSet:
                        if change.name == 'info':
                            state = change.val.state
                        elif change.name == 'info.state':
                            state = change.val
                        else:
                            continue

                        if not str(task) in task_list:
                            continue

                        if state == vim.TaskInfo.State.success:
                            # Remove task from taskList
                            task_list.remove(str(task))
                        elif state == vim.TaskInfo.State.error:
                            raise task.info.error
            # Move to next version
            version = update.version
    finally:
        if pcfilter:
            pcfilter.Destroy()

class ActionGetSenderId(Action):

    def name(self) -> Text:
        return "action_get_sender_id"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        sender_id = tracker.current_state()["sender_id"] 

        dispatcher.utter_message(text="Sender ID: "+sender_id)
        
        return []

class ActionHostnameConfirmation(Action):

    def name(self) -> Text:
        return "action_hostname_confirmation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        vm_name = tracker.get_slot("vm_name")

        
        service_instance = SmartConnect(host=os.getenv("VMWARE_HOST"),
                                            user=os.getenv("VMWARE_USER"),
                                            pwd=os.getenv("VMWARE_PASS"),
                                            port=443,
                                            disableSslCertValidation=True)
        
        vm_info = get_obj(service_instance.content, [vim.VirtualMachine], vm_name)

        if vm_info is None:
            dispatcher.utter_message(text="VM "+vm_name+" gak ketemu nih. info aja ke yang bikin bot")
            dispatcher.utter_message(text="byeee.")
            return [Restarted()]
        elif vm_name is None:
            dispatcher.utter_message(text="Tolong sampaikan ke admin nya bot gagal deteksi nama VM :(")
            return [Restarted()]
        else:
            print("VM "+vm_name)
            ip_address = vm_info.summary.guest.ipAddress
            vm_info_name = vm_info.summary.guest.hostName
            response = "VM: "+vm_info_name+" ("+ip_address+") bukan?"

            dispatcher.utter_message(text=response)


        return []

class ActionGetHostInfo(Action):

    def name(self) -> Text:
        return "action_get_host_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        vm_name = tracker.get_slot("vm_name")

        service_instance = SmartConnect(host=os.getenv("VMWARE_HOST"),
                                            user=os.getenv("VMWARE_USER"),
                                            pwd=os.getenv("VMWARE_PASS"),
                                            port=443,
                                            disableSslCertValidation=True)
        
        vm_info = get_obj(service_instance.content, [vim.VirtualMachine], vm_name)

        if vm_info is None:
            dispatcher.utter_message(text="VM "+vm_name+" gak ketemu nih. info aja ke yang bikin bot")
            dispatcher.utter_message(text="byeee.")
            return [Restarted()]
        else:
            dispatcher.utter_message(text="VM "+vm_name+" ada di host: "+ vm_info.runtime.host.name)
            # # dispatcher.utter_message(text="Kalau sampai 30 menit belum ada respon suruh admin nya ngecek deh")
            # snapshotList = vm_info.snapshot
            # if snapshotList is None:
            #     desc = "Create By Chatbot"
            #     now = datetime.now()
            #     datestr = now.strftime('%Y-%m-%d %H:%M:%S')
            #     task = vm_info.CreateSnapshot_Task(name=datestr,
            #                                 description=desc,
            #                                 memory=True,
            #                                 quiesce=False)

            #     del vm_info
            #     vm_info = vm_info = get_obj(service_instance.content, [vim.VirtualMachine], vm_name)
            #     wait_for_tasks(service_instance, [task])
            #     dispatcher.utter_message(text="Snapshot VM "+vm_name+" status: "+task.info.state)
            # else:
            #     dispatcher.utter_message(text="Masih ada snapshot suruh hapus admin nya yaa...")
        #     raise SystemExit("Unable to locate VirtualMachine.")


        return [Restarted()]    

class ActionSnapshotCreate(Action):

    def name(self) -> Text:
        return "action_snapshot_create"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        vm_name = tracker.get_slot("vm_name")

        service_instance = SmartConnect(host=os.getenv("VMWARE_HOST"),
                                            user=os.getenv("VMWARE_USER"),
                                            pwd=os.getenv("VMWARE_PASS"),
                                            port=443,
                                            disableSslCertValidation=True)
        
        vm_info = get_obj(service_instance.content, [vim.VirtualMachine], vm_name)

        if vm_info is None:
            dispatcher.utter_message(text="VM "+vm_name+" gak ketemu nih. info aja ke yang bikin bot")
            dispatcher.utter_message(text="byeee.")
            return [Restarted()]
        else:
            # dispatcher.utter_message(text="Kita snapshot dulu ya VM "+vm_name)
            # dispatcher.utter_message(text="Kalau sampai 30 menit belum ada respon suruh admin nya ngecek deh")
            snapshotList = vm_info.snapshot
            if snapshotList is None:
                desc = "Create By Chatbot"
                now = datetime.now()
                datestr = now.strftime('%Y-%m-%d %H:%M:%S')
                task = vm_info.CreateSnapshot_Task(name=datestr,
                                            description=desc,
                                            memory=True,
                                            quiesce=False)

                del vm_info
                vm_info = vm_info = get_obj(service_instance.content, [vim.VirtualMachine], vm_name)
                wait_for_tasks(service_instance, [task])
                dispatcher.utter_message(text="Snapshot VM "+vm_name+" status: "+task.info.state)
            else:
                dispatcher.utter_message(text="Masih ada snapshot suruh hapus admin nya yaa...")
        #     raise SystemExit("Unable to locate VirtualMachine.")


        return [Restarted()]
    

class ActionGetResource(Action):

    def name(self) -> Text:
        return "action_get_resource"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        vm_name = tracker.get_slot("vm_name")

        service_instance = SmartConnect(host=os.getenv("VMWARE_HOST"),
                                            user=os.getenv("VMWARE_USER"),
                                            pwd=os.getenv("VMWARE_PASS"),
                                            port=443,
                                            disableSslCertValidation=True)
        

        content = service_instance.RetrieveContent()
        perf_manager = content.perfManager

        # create a mapping from performance stats to their counterIDs
        # counterInfo: [performance stat => counterId]
        # performance stat example: cpu.usagemhz.LATEST
        # counterId example: 6
        counter_info = {}
        for counter in perf_manager.perfCounter:
            full_name = counter.groupInfo.key + "." + \
                        counter.nameInfo.key + "." + counter.rollupType
            counter_info[full_name] = counter.key

        # create a list of vim.VirtualMachine objects so
        # that we can query them for statistics
        container = content.rootFolder
        view_type = [vim.VirtualMachine]
        recursive = True

        container_view = content.viewManager.CreateContainerView(container, view_type, recursive)
        children = container_view.view

        vm_info = get_obj(service_instance.content, [vim.VirtualMachine], vm_name)
        counter_ids = [m.counterId for m in perf_manager.QueryAvailablePerfMetric(entity=vm_info)]

        # Using the IDs form a list of MetricId
        # objects for building the Query Spec
        metric_ids = [vim.PerformanceManager.MetricId(
            counterId=counter, instance="*") for counter in counter_ids]

        # Build the specification to be used
        # for querying the performance manager
        spec = vim.PerformanceManager.QuerySpec(maxSample=1,
                                                entity=vm_info,
                                                metricId=metric_ids)
        # Query the performance manager
        # based on the metrics created above
        result_stats = perf_manager.QueryStats(querySpec=[spec])

        # print(result_stats[0].value)

        output = ""
        whitelist = [
            "cpu.usagemhz.average",
            "mem.usage.average"
        ]
        for val in result_stats[0].value:
            counterinfo_k_to_v = list(counter_info.keys())[
                            list(counter_info.values()).index(val.id.counterId)]
            

            if val.id.instance == '':
                if (counterinfo_k_to_v in whitelist):
                    if counterinfo_k_to_v == "cpu.usagemhz.average":
                        output += "%s: %s\n" % (
                            "Rata rata penggunaan CPU (MHz)", str(val.value[0]))
                    elif counterinfo_k_to_v == "mem.usage.average":
                        output += "%s: %s\n" % (
                            "Rata rata penggunaan Memory (MB)", str(val.value[0]))
                    
            # else:
            #     output += "%s (%s): %s\n" % (
            #         counterinfo_k_to_v, val.id.instance, str(val.value[0]))
                
        # print(output)
        dispatcher.utter_message(text=output)

        # # Loop through all the VMs
        # for child in children:
        #     # Get all available metric IDs for this VM


            

        #     # Loop through the results and print the output
        #     output = ""
        #     for _ in result_stats:
        #         output += "name:        " + child.summary.config.name + "\n"
        #         for val in result_stats[0].value:
        #             # python3
        #             if sys.version_info[0] > 2:
        #                 counterinfo_k_to_v = list(counter_info.keys())[
        #                     list(counter_info.values()).index(val.id.counterId)]
        #             # python2
        #             else:
        #                 counterinfo_k_to_v = counter_info.keys()[
        #                     counter_info.values().index(val.id.counterId)]
        #             if val.id.instance == '':
        #                 output += "%s: %s\n" % (
        #                     counterinfo_k_to_v, str(val.value[0]))
        #             else:
        #                 output += "%s (%s): %s\n" % (
        #                     counterinfo_k_to_v, val.id.instance, str(val.value[0]))

        #     print(output)
            
            # vm_info = get_obj(service_instance.content, [vim.VirtualMachine], vm_name)

            # if vm_info is None:
            #     dispatcher.utter_message(text="VM "+vm_name+" gak ketemu nih. info aja ke yang bikin bot")
            #     dispatcher.utter_message(text="byeee.")
            # else:
                

        return [Restarted()]
