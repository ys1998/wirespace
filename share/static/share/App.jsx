import React from 'react';
import axios from 'axios';				//AJAX requests
import classNames from 'classnames';	//manipulating fields/classes
import qs from 'query-string';			//stringify - for content type application/x-www-form-urlencoded
import ReactDOM from 'react-dom';

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

//https://developer.mozilla.org/en-US/docs/Web/API/FormData/append
//https://stackoverflow.com/questions/39254562/csrf-with-django-reactredux-using-axios/44479078#44479078

//Handling each file and folder
class UnitTemplate extends React.Component{
	constructor(props){
		super(props);
	}

	handleRightClick(event) {
		if(!this.props.isSelected)	this.props.addSelection(event, this.props.link, this.props.actions, () => {this.props.renderMenu(event);});
		else 	this.props.renderMenu(event);
	}

	handleDragStart(event){
		event.stopPropagation();
		if(!this.props.isSelected)	this.props.addSelection(event, this.props.link, this.props.actions);
	}

	handleDrop(event){
		//event.preventDefault();
		if(event.dataTransfer.items == null || event.dataTransfer.items.length == 0){
			if(this.props.type == "Folders")	this.props.moveTo(this.props.link);
			// this.refs.unit.style.opacity = '1';
			event.stopPropagation();
		}
	}

	handleDragOver(event){
		event.preventDefault();
		// this.refs.unit.style.opacity = '0.4';
	}

	handleDragLeave(event){
		event.preventDefault();
		// this.refs.unit.style.opacity = '1';
	}

	handleDragExit(event){
		event.preventDefault();
		// this.refs.unit.style.opacity = '1';
	}

	handleDragEnd(event){
		// this.refs.unit.style.opacity = '1';
	}

	componentDidMount(){
		//this.refs.unit.addEventListener('dragstart', this.handleDragStart);
		//this.refs.unit.addEventListener('drop', this.handleDrop);
	}

	componentWillUnmount(){
		//this.refs.unit.removeEventListener('dragstart', this.handleDragStart);
		//this.refs.unit.removeEventListener('drop', this.handleDrop);
	}

	render() {
		let classes = classNames("w3-transparent", "list-card", "hover-google-blue", {"perma-google-blue" : this.props.isSelected});
		return (
			<div
				className={classes}
				onClick={(e) => {e.stopPropagation(); this.props.addSelection(e, this.props.link, this.props.actions);}}
				onDoubleClick={() => this.props.open(this.props.link)}
				onContextMenu={(e) => this.handleRightClick(e)}
				onDragStart={(e) => this.handleDragStart(e)}
				onDrop={(e) => this.handleDrop(e)}
				onDragOver={(e) => this.handleDragOver(e)}
				onDragLeave={(e) => this.handleDragLeave(e)}
				onDragEnd={(e) => this.handleDragEnd(e)}		//Be careful of this hack if changing DragLeave
				draggable='true'
				ref='unit'
			>
				<i className={classNames("fa", this.props.icon, "fa-5x", "fa-fw", "icon")}></i>
				<div className="w3-container w3-center itemlabel">{this.props.name}</div>
			</div>)
	}
}

//rendering files and folders
class ContentTemplate extends React.Component{
	render(){
		return (
				<div id={this.props.heading}>		
					{this.props.objects.map((object, index) => {
						return (
							<UnitTemplate
								name={object['name']}
								icon={object['icon']}
								open={object['open']}
								link={object['link']}
								key={object['link'] + this.props.heading}
								type={this.props.heading}
								actions={object['actions']}
								isSelected={object['isSelected']}
								moveTo={this.props.moveTo}
								renderMenu={this.props.renderMenu}
								addSelection={this.props.addSelection}
								clearSelection={this.props.clearSelection}
							/>);
					})}
				</div>
			);
	}
}

//process folders for rendering
class Folders extends React.Component{
	constructor(props){
		super(props);
	}
	process(key){
		const folder = this.props.folders[key];
		return ({
			name: this.genName(folder),
			icon: this.genIcon(folder),
			link: key,
			open: this.props.open,
			actions: this.genAction(key),
			isSelected: this.props.selectedList.includes(key),
		})
	}
	genAction(file_link){
		return{
			Open: this.props.open,
			Rename: this.props.rename,
			Download: this.props.download,
			Delete: this.props.delete,
		}
	}

	genName(folder_name){
		return folder_name.slice(0,20);
	}
	genIcon(folder_name){
		return "fa-folder"
	}
	render() {
		if(!this.props.folders)	return;

		const keys = Object.keys(this.props.folders);
		const objects = keys.map((key) => { return this.process(key);});
		return (
			<ContentTemplate
				heading="Folders"
				objects={objects}
				moveTo={this.props.moveTo}
				renderMenu={this.props.renderMenu}
				addSelection={(e, l, a) => this.props.addSelection(e, l, a)}
				clearSelection={this.props.clearSelection}
			/>);
	}
}

//Process files for rendering
class Files extends React.Component{
	process(key){
		const file = this.props.files[key];
		return ({
			name: this.genName(file),		//Name to be displayed
			icon: this.genIcon(file),		//Icon
			link: key,						//Complete path
			open: this.props.open,			//Open method
			actions: this.genAction(key),	//All possible actions for given entity
			isSelected: this.props.selectedList.includes(key),
		})
	}

	genAction(file_link){
		return{
			Open: this.props.open,
			Rename: this.props.rename,
			Download: this.props.download,
			Delete: this.props.delete,
		}
	}

	genIcon(file_name){
		const file = file_name.toLowerCase();
		if(file.endsWith('.pdf'))
			return "fa-file-pdf-o";
		if(file.endsWith('.doc') || file.endsWith('.docx'))
			return "fa-file-word-o";
		if(file.endsWith('.xls') || file.endsWith('.xlsx'))
			return "fa-file-excel-o";
		if(file.endsWith('.ppt') || file.endsWith('.pptx'))
			return "fa-file-powerpoint-o";
		if(file.endsWith('.txt') || file.endsWith('.rtf'))
			return "fa-file-text-o";
		if(file.endsWith('.wav') || file.endsWith('.mp3') || file.endsWith('.aac') || file.endsWith('.wma'))
			return "fa-file-audio-o";
		if(file.endsWith('.jpg') || file.endsWith('.jpeg') || file.endsWith('.bmp') || file.endsWith('.png') || file.endsWith('.gif'))
			return "fa-file-image-o";
		if(file.endsWith('.cpp') || file.endsWith('.c') || file.endsWith('.java') || file.endsWith('.hs') || file.endsWith('.py') || file.endsWith('.php'))
			return "fa-file-code-o";
		if(file.endsWith('.mp4') || file.endsWith('.mov') || file.endsWith('.3gp') || file.endsWith('.avi') || file.endsWith('.flv') || file.endsWith('.wmv'))
			return "fa-file-video-o";
		if(file.endsWith('.tar.gz') || file.endsWith('.zip') || file.endsWith('.rar'))
			return "fa-file-archive-o";
		return "fa-file-o";
	}

	genName(file_name){
		const len = file_name.length;
		if(len < 21)	return file_name;
		return file_name.slice(0,18) + ".." + file_name.slice(len-4,len);
	}

	render() {
		if(!this.props.files)	return;

		const keys = Object.keys(this.props.files);
		const objects = keys.map((key) => {return this.process(key);});
		return (
			<ContentTemplate
				heading="Files"
				objects={objects}
				moveTo={this.props.moveTo}
				renderMenu={this.props.renderMenu}
				addSelection={(e, l, a) => this.props.addSelection(e, l, a)}
				clearSelection={this.props.clearSelection}
			/>);
	}
}

class Content extends React.Component{
	constructor(props){
		super(props);
		this.state = {
			selected: [],
			actions: [],
		}
		this.addSelection = this.addSelection.bind(this);
	}

	addSelection(event, link, actions, callback){
		if(event.ctrlKey || event.altKey || event.shiftKey){
			var newState;
			var selected = this.state.selected;
			var sactions = this.state.actions;
			if(!selected.includes(link)){
				selected.push(link);
				sactions.push(actions);
				newState = {selected: selected, actions: sactions};
			}
		}
		else{
			var selected = this.state.selected;
			if(selected.length == 1 && selected[0] == link)	newState = {selected: [], actions: []};
			else newState = {selected: [link], actions: [actions]};
		}

		if(callback == null){	this.setState(newState);}
		else 	this.setState(newState, () => {callback();});
	}

	clearSelection(){
		this.setState({'selected': [], 'actions': []});
	}

	moveTo(target){
		const list = this.state.selected;
		if(list.includes(target))	return false;
		for(var i = 0; i < list.length; i++)	this.props.move(list[i],target);
		this.clearSelection();
	}

	render(){
		return (
			<div className="w3-container w3-light-gray ContentStyle" onClick={() => this.clearSelection()}>
				<Folders
					folders={this.props.folders}
					open={this.props.openFolder}
					rename={this.props.rename}
					delete={this.props.delete}
					download={this.props.download}
					moveTo={(e) => this.moveTo(e)}
					renderMenu={(e) => this.props.renderMenu(e, this.state.selected, this.state.actions)}
					selectedList={this.state.selected}
					addSelection={(e, l, a) => this.addSelection(e, l, a)}
					clearSelection={this.clearSelection}
				/>
				<Files
					files={this.props.files}
					open={this.props.openFile}
					rename={this.props.rename}
					delete={this.props.delete}
					download={this.props.download}
					moveTo={(e) => this.moveTo(e)}
					renderMenu={(e) => this.props.renderMenu(e, this.state.selected, this.state.actions)}
					selectedList={this.state.selected}
					addSelection={(e, l, a) => this.addSelection(e, l, a)}
					clearSelection={this.clearSelection}
				/>
			</div>);
	}
}

//Options for uploading files and creating folders
class ActionButton extends React.Component{
	componentDidMount(){
		if('webkitdirectory' in document.createElement('input'))
			this.refs.inputFolder.setAttribute('webkitdirectory', '');
		else{
			this.refs.labelFolder.className += " w3-disabled";
			this.refs.inputFolder.setAttribute('disabled', '');
		}
	}

	render(){
		return (
			<div className="w3-col w3-left ActionBoxStyle">
				<label id="options" className="w3-dropdown-hover Actionbuttonstyle">
					<button className="w3-button google-blue hover-google-blue w3-bar Actionbold">NEW</button>
					<div className="w3-dropdown-content w3-bar-block w3-border Actionlong">
						<label className="w3-button w3-bar-item light-emph">
							<input
								type="file" id="uplist"
								className="w3-button"
								onChange={() => this.props.uploadFile()}
								multiple/>
							<i className={classNames('fa','fa-upload','ActionIcon')}></i>Upload File
						</label>
						<label className="w3-button w3-bar-item light-emph w3-border-bottom" ref='labelFolder'>
							<input
								type="file" id="ufolder"
								onChange={() => this.props.uploadFolder()}
								ref='inputFolder'/>
							<i className={classNames('fa','fa-upload','ActionIcon')}></i>Upload Folder
						</label>
						<label className="w3-button w3-bar-item light-emph"
								onClick={() => this.props.createFolder()}>
								<i className={classNames('fa','fa-plus','ActionIcon')}></i>New Folder
						</label>
					</div>
				</label>
			</div>
		);
	}
}

//The address bar - each path is clickable and redirects to contents of that folder
class Address extends React.Component{
	genLink(folders){
		var links = Array(folders.length);
		links[folders.length - 1] = this.props.folders;
		for(var i = links.length - 1; i > 0; i--){
			links[i - 1] = links[i] + '/..';
		}
		return links;
	}

	renderFolder(name, link, last){
		let display;
		if(last)	display = <b>{name}</b>
		else		display = name
		return (
			<button className="w3-button w3-hover-white AddressStyle" onClick={() => this.props.jumpTo(link)}>
				{display}
			</button>
			);
	}

	render() {
		const folders = this.props.folders.split('/');
		const links = this.genLink(folders);

		return (
			<div className="w3-rest scroll-x">
				<div className="AddressBoxStyle">
					{folders.map((name, index) => {
						return 	(
							<div className="AddressOuterStyle" key={name}>
							{index + 1 == folders.length ?
								this.renderFolder(name, links[index], true) :
								this.renderFolder(name, links[index], false)}
							<i className="fa fa-chevron-right AddressIconStyle"></i>
							</div>
							);
					})}
				</div>
			</div>);
	}
}

//Download all contents of open directory
class DownAll extends React.Component{
	shouldComponentUpdate(nextProps, nextState){
		return false;
	}

	render(){
		return (
			<div id="down_all" className="circle w3-button w3-right w3-col w3-hover-gray w3-button DownAllStyle">
				<i className="fa fa-download" onClick={() => this.props.onClick()}></i>
			</div>
			);
	}
}

//Search bar - search as you type : currently suffers from overload
class SearchBar extends React.PureComponent{
	render(){
		return (
			<div className="w3-rest SearchBarStyle">
				<input id="searchBar" className="w3-input w3-light-gray w3-border-0 SearchBarBoxStyle" type="text" placeholder="Search storage" onChange={() => this.props.search()} />
			</div>
			);
	}
}

//WIRESPACE (github link)
class ProjectLogo extends React.Component{
	shouldComponentUpdate(nextProps, nextState){
		return false;
	}

	render(){
		const projectLink = "https://github.com/ys1998/Wirespace"
		return (
			<div className="w3-col w3-left w3-hover-white LogoBoxStyle">
				<a href={projectLink} className="w3-button w3-round w3-hover-white LogoStyle">Wirespace</a>
			</div>
		);
	}
}

//Action button, address
function NavBot(props){
	return (
		<div className="w3-row NavBotStyle">
			<ActionButton
				uploadFile={props.uploadFile}
				uploadFolder={props.uploadFolder}
				createFolder={props.createFolder}
			/>
			<Address
				folders={props.folders}
				jumpTo={props.jumpTo}
			/>
		</div>
		);
}

//Title, search bar and download all
function NavTop(props){
	return (
		<div className="w3-row NavTopStyle">
			<ProjectLogo />
			<DownAll onClick={() => props.downloadAll()} />
			<SearchBar search={props.search} />
		</div>
		);
}


//The white header/navigation bar
function NavBar(props){
	return (
		<div className="w3-white NavBarOuterStyle">
			<div className="w3-block w3-card NavBarStyle">
				<NavTop
					downloadAll={props.download}
					search={props.search}
				/>
				<NavBot
					folders={props.folders}
					jumpTo={props.jumpTo}
					uploadFile={props.uploadFile}
					uploadFolder={props.uploadFolder}
					createFolder={props.createFolder}
				/>				
			</div>
		</div>
		);
}

function Icons(props){
	return <div></div>
}

//Root of rendering the entire GUI
class App extends React.Component {
	constructor() {
		super();
		this.state = {
			dirs: {},
			files: {},
			path: '',
			hidden: {},
			menuHidden: true,
		};
		this.baseURL = '';
		this.hideMenu = this.hideMenu.bind(this);
		this.escFunction = this.escFunction.bind(this);
	}

	//Request template for opening folders
	get_request(target){
		axios.post(this.baseURL + 'open/',
			qs.stringify({
				target: target,
			}), {
				headers: {
					'Content-Type': 'application/x-www-form-urlencoded',
				}
			})
      	.then(res => {
      		const newState = {
      			path: res.data.path,
      			dirs: res.data.dirs,
      			files: res.data.files,
      			hidden: res.data.hidden,
      		};
      		this.setState(newState);
      })
      	.catch(error => {
      		console.log("Error in opening");
      		console.log(error);
      	});
	}

	//Handling search
	handleSearch(){
		const query = document.getElementById('searchBar').value;
		if(query != ''){
			//console.log(query);
			axios.post(this.baseURL + 'search/',
				qs.stringify({
					address: this.state.path,
					query: query,
				}), {
					headers: {
						'Content-Type': 'application/x-www-form-urlencoded',
					}
				})
			.then(res => {
				const newState = {
					dirs: res.data.dirs,
					files: res.data.files,
					hidden: res.data.hidden,
				};
				this.setState(newState);
			})
			.catch(error => {
				console.log("Error in request");
				console.log(error);
			});
		}
		else this.get_request(this.state.path)
	}

	//Open new file/folder (for search results)
	jumpTo(address){
		this.get_request(address);
	}

	//Open folder
	openFolder(folder){
		this.get_request(folder);
	}

	//Open file
	openFile(address){
		var form = document.forms['openform'];
		form.elements[0].value = address
		form.submit();
	}

	//Download files
	download(addresses){
		//Use hidden form to send post requests for download
		if(!(addresses.constructor === Array))	addresses = [addresses];
		var form = document.forms['downloadform'];
		var len = form.childNodes.length;
		for(var i = 0; i < addresses.length; i++){
			var input = document.createElement('input');
			input.type = 'text';
			input.name = 'target[]';
			input.value = addresses[i];
			form.appendChild(input);
		}
		form.submit();
		for(var i = form.childNodes.length; i > len; i--)	form.removeChild(form.lastChild);
	}

	upload(files, addresses){
		var formData = new FormData();
		for(var i = 0; i < files.length; i++){
			formData.append('uplist[]', files[i]);
			formData.append('address[]', addresses[i]);
		}
		axios.post(this.baseURL + 'upload/', formData, {
			headers: {
				'Content-Type': 'multipart/form-data'
			}
		}).then(res => {
			this.get_request(this.state.path);
		}).catch(err => {
			alert("Error in uploading files. See console log for more details")
		});
	}

	//Upload multiple files
	uploadFile(){
		var files = document.querySelector('#uplist').files;
		var addr = [];
		for(var i = 0; i < files.length; i++)	addr[i] = this.state.path + '/' + files[i].name;
		this.upload(files, addr);
	}

	//Upload folder. Supported in very few browsers
	uploadFolder(){
		var files = document.querySelector('#ufolder').files;
		var addr = []
		for(var i = 0; i < files.length; i++){
			addr[i] = this.state.path + '/' + files[i].webkitRelativePath;
		}
		this.upload(files, addr);
	}

	//Create folders
	createFolder(){
		var name = prompt("Name of the new folder:");
		if(name == null || name == "")	return;
		axios.post(this.baseURL + 'create_folder/',
			qs.stringify({
				address: this.state.path,
				folder_name: name,
			}), {
				headers: {
					'Content-Type': 'application/x-www-form-urlencoded',
				}
			})
      	.then(res => {
      		this.get_request(this.state.path)
      	})
      	.catch(error => {
      		console.log(error);
      		alert("Error in creating folder. Please check console for more details");
      	});
	}

	//Delete file/folder
	delete(link){
		var sure = confirm("Warning: Contents will be permanently deleted. Are you sure you want to delete this?")
		if(!sure)	return;
		if(!(link.constructor === Array))	link = [link];
		
		var formData = new FormData();

		for(var i = 0; i < link.length; i++)	formData.append('address[]', link[i]);
		axios.post(this.baseURL + 'delete/', formData, {
				headers: {
					'Content-Type': 'application/x-www-form-urlencoded',
				}
			})
      	.then(res => {
      		this.get_request(this.state.path)
      	})
      	.catch(error => {
      		console.log(error);
      		alert("Error in deleting. Please check console for more details");
      	});
	}

	//Move file/folder from src to dest:
	move(src, dst){
		axios.post(this.baseURL + 'move/',
			qs.stringify({
				source: src,
				target: dst,
			}), {
				headers: {
					'Content-Type': 'application/x-www-form-urlencoded',
				}
			})
      	.then(res => {
      		this.get_request(this.state.path)
      	})
      	.catch(error => {
      		console.log(error);
      		alert("Error in moving. Please check console for more details");
      	});
	}

	//Rename
	rename(link){
		var name = prompt("Enter new name");
		if(name == null || name == "")	return;
		axios.post(this.baseURL + 'move/',
			qs.stringify({
				source: link,
				target: this.state.path + '/' + name,
			}), {
				headers: {
					'Content-Type': 'application/x-www-form-urlencoded',
				}
			})
      	.then(res => {
      		this.get_request(this.state.path)
      	})
      	.catch(error => {
      		console.log(error);
      		alert("Error in renaming. Please check console for more details");
      	});
	}

	execute(targets, action){
		for(var i = 0; i < targets.length; i++)	action(targets[i]);
	}

	//Render the context menu
	renderMenu(event, targets, actions){
		this.setState({menuHidden: false});
		const classes = classNames("context-menu", "w3-bar-block", "w3-card-2", "w3-white");
		const dStyle = {
			position: 'absolute',
			top: event.clientY,
			left: event.clientX
		}
		if(targets.length == 0 || targets.length == 1){
			ReactDOM.render(
				<div id="menu" className = {classes} style = {dStyle}>
					{targets == [] ? <div className = "w3-button w3-bar-item">No option</div> : Object.keys(actions[0]).map((name, index) => {
						return (
							<div
								className="w3-button w3-bar-item"
								onClick={() => {actions[0][name](targets[0]), this.hideMenu()}}
								key={index}
							>
							{name}
							</div>
							);
					})}
				</div>
				, document.getElementById('menu'));
		}
		else {
			ReactDOM.render(
				<div id="menu" className = {classes} style = {dStyle}>
					{targets == [] ? <div className = "w3-button w3-bar-item">No option</div> : ['Download', 'Delete'].map((action, index) => {
						return (
							<div
								className="w3-button w3-bar-item"
								onClick={() => {actions[0][action](targets); this.hideMenu()}}
								key={index}
							>
							{action}
							</div>
							);
					})}
				</div>
				, document.getElementById('menu'));
		}
		
	}

	//Hide the context menu
	hideMenu(event){
		this.setState({menuHidden: true});
		ReactDOM.render(<div id="menu" className="hidden"></div>, document.getElementById('menu'));
	}

	escFunction(event){
		if(event.keyCode == 27)	this.hideMenu(event);
	}

	// scanfiles(item, address, list){
	// 	if (item.isFile) {
	// 		item.file(file => {list.files.push(file); console.log(file);}
	// 			);
	// 		list.addresses.push(address + '/' + item.name);
	// 		return list;
	// 	}
	// 	else if (item.isDirectory) {
	// 		let directoryReader = item.createReader();
	// 		directoryReader.readEntries((entries) => {
	// 			entries.forEach((entry) => {
	// 				var m = this.scanfiles(entry, address + '/' + item.name, list);
	// 				list.addresses.concat(m.addresses);
	// 				list.files.concat(m.files);
	// 			});
	// 		});
	// 		return list;
	// 	}
	// }

	handleDrop(event){
		event.preventDefault();
		const items=event.dataTransfer.files;
		if(items == null || items.length == 0)	return;
		let address=[]
		for(var i = 0; i < items.length; i++){
			address[i] = this.state.path + '/' + items[i].name;
			//let item = items[i].webkitGetAsEntry()
		}
		this.upload(items,address);
		// const items = event.dataTransfer.items;
		// if(items == null || items.length == 0)	return;
		// let list = {addresses: [], files: []};
		// for(var i = 0; i < items.length; i++){
		// 	var m = this.scanfiles(items[i].webkitGetAsEntry(), this.state.path, list);
		// 	list.addresses.concat(m.addresses);
		// 	list.files.concat(m.files);
		// }
		// console.log(list.addresses);
		// console.log(list.files);
		// console.log(list);
		// this.upload(list.files, list.addresses);
	}

	handleDragOver(event){
		event.preventDefault();
		// this.refs.app.style.opacity = '0.5';
		// this.refs.app.style.border = '5px dashed blue';
	}

	handleDragEnd(event){
		event.preventDefault();
		// this.refs.app.style.opacity = '1';
		// this.refs.app.style.border = '';
	}

	//Request for data at shared directory on mounting
	componentDidMount(){
		document.addEventListener("keyup",  this.escFunction);
		this.get_request('');
	}

	componentWillUnmount(){
		document.removeEventListener("keyup", this.escFunction);
	}

	render() {
		return (
				<div
					className="full-body"
					onClick={(e) => this.hideMenu(e)}
					onDoubleClick={(e) => {e.preventDefault();}}
					onContextMenu={(e) => {e.preventDefault();}}	//Override default right-click behavior
					onSelect={(e) => {e.preventDefault();}}
					onDragOver={(e) => this.handleDragOver(e)}
					onDragEnd={(e) => this.handleDragEnd(e)}
					onDragLeave={(e) => this.handleDragEnd(e)}
					onDrop={(e) => this.handleDrop(e)}
					ref='app'
				>
					<div>
					<NavBar
						folders={this.state.path}
						search={query => this.handleSearch(query)}
						download={() => this.download(this.state.path)}
						jumpTo={address => this.jumpTo(address)}
						uploadFile={() => this.uploadFile()}
						uploadFolder={() => this.uploadFolder()}
						createFolder={() => this.createFolder()}
						search={query => this.handleSearch(query)}
						hide={(e) => this.hideMenu(e)}
					/>
					</div>
					<Icons
						/*Handle click events*/
					/>
					<div>
					<Content
						folders={this.state.dirs}
						openFile={address => this.openFile(address)}
						files={this.state.files}
						openFolder={address => this.openFolder(address)}
						rename={address => this.rename(address)}
						move={(s,d) => this.move(s,d)}
						delete={address => this.delete(address)}
						download={address => this.download(address)}
						renderMenu={(e, l, t) => this.renderMenu(e, l, t)}
					/>
					</div>
			 	</div>
				);
	}
}

export default App;
